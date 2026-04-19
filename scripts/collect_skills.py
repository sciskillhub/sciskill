#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
import yaml

API_ROOT = "https://api.github.com"
API_VERSION = "2022-11-28"
SEARCH_PAGE_DELAY_SECONDS = 2.5
RATE_LIMIT_BUFFER_SECONDS = 1
SUBPROCESS_OUTPUT_LIMIT = 4000
EXCLUDED_REPO_FULL_NAMES = {
    "sciskillhub/sciskill",
}
MANIFEST_FILENAME = "skill-manifest.json"
GITMODULES_FILENAME = ".gitmodules"
REGISTRY_MARKDOWN_FILENAME = "open-source-skills.md"


@dataclass
class SkillMatch:
    repo_full_name: str
    default_branch: str
    skill_path: str
    front_matter: Dict[str, Any]
    repo_html_url: str


@dataclass
class QuerySpec:
    query: str
    domain_topic: Optional[str] = None
    qualifier_topic: Optional[str] = None
    legacy_topic: Optional[str] = None


class CloneError(RuntimeError):
    def __init__(self, full_name: str, attempts: List[Dict[str, Any]]):
        super().__init__(f"Clone failed for {full_name}")
        self.attempts = attempts


def gh_headers(token: str) -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "sciskill-skill-collector/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_error_message(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip()

    message = payload.get("message")
    if isinstance(message, str):
        return message.strip()
    return response.text.strip()


def rate_limit_wait_seconds(response: requests.Response) -> int:
    retry_after_header = response.headers.get("Retry-After")
    if retry_after_header and retry_after_header.isdigit():
        return max(int(retry_after_header), RATE_LIMIT_BUFFER_SECONDS)

    reset_header = response.headers.get("X-RateLimit-Reset")
    if reset_header and reset_header.isdigit():
        reset_epoch = int(reset_header)
        wait_seconds = reset_epoch - int(time.time()) + RATE_LIMIT_BUFFER_SECONDS
        if wait_seconds > 0:
            return wait_seconds

    message = github_error_message(response).lower()
    if "secondary rate limit" in message or "rate limit exceeded" in message:
        return 60

    return 0


def log_rate_limit_wait(url: str, response: requests.Response, wait_seconds: int) -> None:
    resource = response.headers.get("X-RateLimit-Resource", "api")
    reset_header = response.headers.get("X-RateLimit-Reset")
    reset_note = ""
    if reset_header and reset_header.isdigit():
        reset_time = datetime.utcfromtimestamp(int(reset_header)).strftime("%Y-%m-%d %H:%M:%S UTC")
        reset_note = f" (reset at {reset_time})"
    print(
        f"[INFO] GitHub {resource} rate limit hit for {url}; waiting {wait_seconds}s{reset_note}",
        file=sys.stderr,
    )


def gh_get(url: str, token: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    last_error: Optional[Exception] = None
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers=gh_headers(token), params=params, timeout=40)
            if r.status_code in {502, 503, 504} and attempt < 3:
                time.sleep(attempt)
                continue
            r.raise_for_status()
            return r
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            is_retryable = status_code in {403, 429, 502, 503, 504}
            last_error = exc
            if is_retryable and attempt < 3:
                wait_seconds = 0
                if exc.response is not None:
                    wait_seconds = rate_limit_wait_seconds(exc.response)
                    if wait_seconds > 0 and status_code in {403, 429}:
                        log_rate_limit_wait(url, exc.response, wait_seconds)
                time.sleep(max(wait_seconds, attempt))
                continue
            break
        except requests.RequestException as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt)
                continue
            break

    assert last_error is not None
    raise last_error


def read_topics_from_file(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"topics file not found: {path}")

    topics: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        topics.append(line)
    return topics


def parse_topics_arg(raw: str) -> List[str]:
    if not raw.strip():
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def normalize_topics(topics: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for t in topics:
        t2 = t.strip()
        if not t2:
            continue
        if t2 not in seen:
            seen.add(t2)
            out.append(t2)
    return out


def build_queries(
    base_query: str,
    domain_topics: List[str],
    qualifier_topics: List[str],
    legacy_topics: Optional[List[str]] = None,
) -> List[QuerySpec]:
    """
    返回查询规格：
    - 新模式：domain topic × qualifier topic 的笛卡尔积，且查询中必须同时包含两个 topic
    - 兼容旧模式：只有单一 topic 列表时，按旧逻辑逐个扩展
    """
    base_query = base_query.strip()
    domain_topics = normalize_topics(domain_topics)
    qualifier_topics = normalize_topics(qualifier_topics)
    legacy_topics = normalize_topics(legacy_topics or [])

    has_dual_topic_mode = bool(domain_topics or qualifier_topics)
    if has_dual_topic_mode and (not domain_topics or not qualifier_topics):
        raise ValueError("domain topics 和 qualifier topics 必须同时提供，才能启用双 topic AND 收集模式")

    if has_dual_topic_mode:
        queries: List[QuerySpec] = []
        for domain_topic in domain_topics:
            for qualifier_topic in qualifier_topics:
                clauses = [base_query] if base_query else []
                clauses.extend([f"topic:{domain_topic}", f"topic:{qualifier_topic}"])
                queries.append(
                    QuerySpec(
                        query=" ".join(clauses),
                        domain_topic=domain_topic,
                        qualifier_topic=qualifier_topic,
                    )
                )
        return queries

    if not legacy_topics:
        return [QuerySpec(query=base_query)]

    queries: List[QuerySpec] = []
    for topic in legacy_topics:
        if base_query:
            queries.append(QuerySpec(query=f"{base_query} topic:{topic}", legacy_topic=topic))
        else:
            queries.append(QuerySpec(query=f"topic:{topic}", legacy_topic=topic))
    return queries


def empty_repo_topic_state() -> Dict[str, Set[Any]]:
    return {
        "domains": set(),
        "qualifiers": set(),
        "pairs": set(),
        "legacy_topics": set(),
    }


def build_repo_topic_payload(state: Optional[Dict[str, Set[Any]]]) -> Dict[str, Any]:
    if not state:
        return {
            "matched_domain_topics": [],
            "matched_qualifier_topics": [],
            "matched_topic_pairs": [],
            "matched_topics": [],
        }

    pairs = sorted(state["pairs"])
    return {
        "matched_domain_topics": sorted(state["domains"]),
        "matched_qualifier_topics": sorted(state["qualifiers"]),
        "matched_topic_pairs": [
            {"domain_topic": domain_topic, "qualifier_topic": qualifier_topic}
            for domain_topic, qualifier_topic in pairs
        ],
        "matched_topics": sorted(state["legacy_topics"]),
    }


def is_excluded_repo(full_name: Optional[str]) -> bool:
    if not full_name:
        return False
    full_name = full_name.strip()
    if full_name.lower() in EXCLUDED_REPO_FULL_NAMES:
        return True
    if full_name.lower().startswith("sciskillhub/"):
        return True
    return False


def search_repositories(
    token: str,
    query: str,
    max_repos: int = 50,
    sort: str = "updated",
    order: str = "desc",
) -> List[Dict[str, Any]]:
    repos: List[Dict[str, Any]] = []
    page = 1

    while len(repos) < max_repos:
        per_page = min(100, max_repos - len(repos))
        r = gh_get(
            f"{API_ROOT}/search/repositories",
            token,
            params={
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page,
                "page": page,
            },
        )
        data = r.json()
        raw_items = data.get("items", [])
        # Search API has a much lower per-minute quota than the core REST API.
        time.sleep(SEARCH_PAGE_DELAY_SECONDS)
        if not raw_items:
            break

        items = [repo for repo in raw_items if not is_excluded_repo(repo.get("full_name"))]

        repos.extend(items)
        if len(raw_items) < per_page:
            break
        page += 1

    return repos[:max_repos]


def summarize_request_error(exc: Exception) -> str:
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        body = exc.response.text.strip().replace("\n", " ")
        if len(body) > 300:
            body = body[:300] + "..."
        return f"HTTP {exc.response.status_code}: {body}"
    return str(exc)


def dedupe_repos(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: Set[str] = set()
    out: List[Dict[str, Any]] = []
    for repo in repos:
        full_name = repo.get("full_name")
        if not full_name or full_name in seen or is_excluded_repo(full_name):
            continue
        seen.add(full_name)
        out.append(repo)
    return out


def get_repo_info(token: str, full_name: str) -> Tuple[str, str]:
    r = gh_get(f"{API_ROOT}/repos/{full_name}", token)
    data = r.json()
    return data["default_branch"], data["html_url"]


def get_recursive_tree(token: str, full_name: str, branch: str) -> List[Dict[str, Any]]:
    r_ref = gh_get(f"{API_ROOT}/repos/{full_name}/branches/{branch}", token)
    ref_data = r_ref.json()
    tree_sha = ref_data["commit"]["commit"]["tree"]["sha"]

    r_tree = gh_get(
        f"{API_ROOT}/repos/{full_name}/git/trees/{tree_sha}",
        token,
        params={"recursive": "1"},
    )
    tree_data = r_tree.json()
    return tree_data.get("tree", [])


def get_file_content(token: str, full_name: str, path: str, ref: str) -> str:
    r = gh_get(
        f"{API_ROOT}/repos/{full_name}/contents/{path}",
        token,
        params={"ref": ref},
    )
    data = r.json()

    if data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")

    download_url = data.get("download_url")
    if download_url:
        rr = requests.get(download_url, timeout=40)
        rr.raise_for_status()
        return rr.text

    raise RuntimeError(f"Unable to read file: {full_name}:{path}")


def extract_front_matter(md_text: str) -> Optional[Dict[str, Any]]:
    text = md_text.lstrip("\ufeff")
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not m:
        return None

    raw_yaml = m.group(1)
    try:
        data = yaml.safe_load(raw_yaml)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None
    return data


def make_json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]
    return value


def validate_skill_md(md_text: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    fm = extract_front_matter(md_text)
    if fm is None:
        return False, "missing or invalid YAML front matter", None

    name = fm.get("name")
    description = fm.get("description")

    if not isinstance(name, str) or not name.strip():
        return False, "front matter missing valid 'name'", fm

    if not re.fullmatch(r"[a-z0-9-]+", name.strip()):
        return False, "invalid 'name' format; expected [a-z0-9-]+", fm

    if not isinstance(description, str) or not description.strip():
        return False, "front matter missing valid 'description'", fm

    if len(description.strip()) < 10:
        return False, "description too short", fm

    return True, "ok", fm


def find_valid_skill_in_repo(token: str, full_name: str) -> List[SkillMatch]:
    default_branch, html_url = get_repo_info(token, full_name)
    tree = get_recursive_tree(token, full_name, default_branch)

    skill_paths = [
        item["path"]
        for item in tree
        if item.get("type") == "blob" and Path(item.get("path", "")).name == "SKILL.md"
    ]

    matches: List[SkillMatch] = []
    for skill_path in skill_paths:
        try:
            content = get_file_content(token, full_name, skill_path, default_branch)
            ok, _, fm = validate_skill_md(content)
            if ok and fm is not None:
                matches.append(
                    SkillMatch(
                        repo_full_name=full_name,
                        default_branch=default_branch,
                        skill_path=skill_path,
                        front_matter=fm,
                        repo_html_url=html_url,
                    )
                )
        except Exception as e:
            print(f"[WARN] failed reading {full_name}:{skill_path}: {e}", file=sys.stderr)

        time.sleep(0.2)

    return matches


def submodule_target_path(sciskill_root: Path, full_name: str) -> Path:
    owner, repo = full_name.split("/", 1)
    return sciskill_root / "open-source" / owner / repo


def git_index_entry(sciskill_root: Path, target_rel: str) -> Optional[Dict[str, str]]:
    result = subprocess.run(
        ["git", "ls-files", "--stage", "--", target_rel],
        cwd=sciskill_root,
        capture_output=True,
        text=True,
        check=False,
    )
    line = (result.stdout or "").strip()
    if not line:
        return None
    try:
        meta, path_text = line.split("\t", 1)
        mode, sha, stage = meta.split()
    except ValueError:
        return None
    return {
        "mode": mode,
        "sha": sha,
        "stage": stage,
        "path": path_text,
    }


def is_registered_submodule(sciskill_root: Path, full_name: str) -> bool:
    target_rel = str(Path("open-source") / full_name)
    entry = git_index_entry(sciskill_root, target_rel)
    return bool(entry and entry.get("mode") == "160000")


def already_added(sciskill_root: Path, full_name: str) -> bool:
    manifest = load_manifest(sciskill_root)
    return any(e.get("fullName") == full_name for e in manifest)


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.exists():
        shutil.rmtree(path, ignore_errors=True)


def submodule_git_dir(sciskill_root: Path, target_rel: str) -> Optional[Path]:
    result = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"],
        cwd=sciskill_root,
        capture_output=True,
        text=True,
        check=False,
    )
    git_common_dir = (result.stdout or "").strip()
    if not git_common_dir:
        return None
    common_dir = Path(git_common_dir)
    if not common_dir.is_absolute():
        common_dir = (sciskill_root / common_dir).resolve()
    return common_dir / "modules" / Path(target_rel)


def cleanup_failed_submodule_add(sciskill_root: Path, target_rel: str) -> None:
    target = sciskill_root / target_rel
    remove_path(target)
    subprocess.run(
        ["git", "rm", "--cached", "-f", "--", target_rel],
        cwd=sciskill_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["git", "config", "--local", "--remove-section", f"submodule.{target_rel}"],
        cwd=sciskill_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    gitmodules = sciskill_root / GITMODULES_FILENAME
    if gitmodules.exists():
        subprocess.run(
            ["git", "config", "--file", GITMODULES_FILENAME, "--remove-section", f"submodule.{target_rel}"],
            cwd=sciskill_root,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not gitmodules.read_text(encoding="utf-8").strip():
            gitmodules.unlink(missing_ok=True)
    modules_dir = submodule_git_dir(sciskill_root, target_rel)
    if modules_dir:
        shutil.rmtree(modules_dir, ignore_errors=True)


def submodule_head_sha(sciskill_root: Path, full_name: str) -> Optional[str]:
    repo_path = submodule_target_path(sciskill_root, full_name)
    if repo_path.exists():
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            result = None
        if result and result.returncode == 0:
            value = (result.stdout or "").strip()
            if value:
                return value

    target_rel = str(Path("open-source") / full_name)
    entry = git_index_entry(sciskill_root, target_rel)
    if entry and entry.get("mode") == "160000":
        value = entry.get("sha", "").strip()
        return value or None
    return None


def truncate_output(text: str, limit: int = SUBPROCESS_OUTPUT_LIMIT) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def default_error_report_path(report_path: Path) -> Path:
    if report_path.name.endswith("_report.json"):
        return report_path.with_name(report_path.name.replace("_report.json", "_errors.json"))
    if report_path.suffix:
        return report_path.with_name(f"{report_path.stem}_errors{report_path.suffix}")
    return report_path.with_name(report_path.name + "_errors.json")


def load_manifest(sciskill_root: Path) -> List[Dict[str, Any]]:
    mp = sciskill_root / MANIFEST_FILENAME
    if not mp.is_file():
        return []
    try:
        data = json.loads(mp.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def external_manifest_path(sciskill_root: Path) -> Path:
    configured = os.environ.get("SCISKILL_DATA_DIR", "").strip()
    data_root = Path(configured).expanduser().resolve() if configured else (sciskill_root.parent / "data").resolve()
    return data_root / MANIFEST_FILENAME


def write_manifest_file(target: Path, payload: str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")


def repair_manifest(sciskill_root: Path) -> bool:
    script_path = Path(__file__).with_name("repair_skill_manifest.py")
    if not script_path.is_file():
        return False
    result = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(sciskill_root)],
        cwd=sciskill_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        message = (result.stdout or "").strip()
        if message:
            print(message)
        return True
    error = (result.stderr or result.stdout or "").strip()
    if error:
        print(f"[WARN] manifest repair failed: {error}", file=sys.stderr)
    return False


def save_manifest(sciskill_root: Path, entries: List[Dict[str, Any]]) -> None:
    entries = sorted(entries, key=lambda e: e.get("fullName", ""))
    payload = json.dumps(entries, indent=2, ensure_ascii=False) + "\n"
    write_manifest_file(sciskill_root / MANIFEST_FILENAME, payload)
    write_manifest_file(external_manifest_path(sciskill_root), payload)


def add_to_manifest(sciskill_root: Path, entry: Dict[str, Any]) -> None:
    entries = load_manifest(sciskill_root)
    full_name = entry.get("fullName", "")
    if any(e.get("fullName") == full_name for e in entries):
        return
    entries.append(entry)
    save_manifest(sciskill_root, entries)


def generate_registry_markdown(sciskill_root: Path) -> None:
    script_path = Path(__file__).with_name("generate_open_source_skills_md.py")
    if not script_path.is_file():
        return
    subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--repo-root",
            str(sciskill_root),
            "--output",
            REGISTRY_MARKDOWN_FILENAME,
            "--cache-root",
            str(sciskill_root.parent / "data" / "open-source"),
        ],
        cwd=sciskill_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def clone_skill_repo(
    sciskill_root: Path,
    full_name: str,
    default_branch: str,
    dry_run: bool = False,
) -> str:
    owner, repo = full_name.split("/", 1)
    https_url = f"https://github.com/{owner}/{repo}.git"
    print(f"[INFO] registry-only mode: record {full_name} -> open-source/{full_name}")
    if dry_run:
        return https_url
    return https_url


def cloned_repo_head_sha(sciskill_root: Path, full_name: str) -> Optional[str]:
    del sciskill_root, full_name
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find GitHub repos containing valid SKILL.md and add them into open-source/ as submodules."
    )
    parser.add_argument("--token", default=os.getenv("GITHUB_TOKEN", ""), help="GitHub token")
    parser.add_argument("--sciskill-root", required=True, help="Local path of sciskill repo")
    parser.add_argument("--query", default="archived:false is:public", help="Base GitHub repository search query")
    parser.add_argument("--topics", default="", help="Legacy comma-separated topics")
    parser.add_argument("--topics-file", default="", help="Legacy path to topics file, one topic per line")
    parser.add_argument("--domain-topics", default="", help="Comma-separated domain topics")
    parser.add_argument("--domain-topics-file", default="", help="Path to domain topics file, one topic per line")
    parser.add_argument("--qualifier-topics", default="", help="Comma-separated skill/agent qualifier topics")
    parser.add_argument("--qualifier-topics-file", default="", help="Path to qualifier topics file, one topic per line")
    parser.add_argument("--max-repos", type=int, default=50, help="Max repos per query")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report", default="reports/skill_report.json")
    parser.add_argument("--error-report", default="", help="Path to save detailed error information")
    args = parser.parse_args()

    if not args.token:
        print("ERROR: missing GitHub token. Set --token or GITHUB_TOKEN", file=sys.stderr)
        return 2

    sciskill_root = Path(args.sciskill_root).resolve()
    if not (sciskill_root / ".git").exists():
        print(f"ERROR: {sciskill_root} does not look like a git repo", file=sys.stderr)
        return 2

    repair_manifest(sciskill_root)

    domain_topics: List[str] = []
    qualifier_topics: List[str] = []
    legacy_topics: List[str] = []

    domain_topics.extend(parse_topics_arg(args.domain_topics))
    qualifier_topics.extend(parse_topics_arg(args.qualifier_topics))
    legacy_topics.extend(parse_topics_arg(args.topics))

    if args.domain_topics_file:
        domain_topics.extend(read_topics_from_file(Path(args.domain_topics_file)))
    if args.qualifier_topics_file:
        qualifier_topics.extend(read_topics_from_file(Path(args.qualifier_topics_file)))
    if args.topics_file:
        legacy_topics.extend(read_topics_from_file(Path(args.topics_file)))

    domain_topics = normalize_topics(domain_topics)
    qualifier_topics = normalize_topics(qualifier_topics)
    legacy_topics = normalize_topics(legacy_topics)

    if (domain_topics or qualifier_topics) and legacy_topics:
        print("ERROR: dual-topic mode 和 legacy --topics/--topics-file 不能混用", file=sys.stderr)
        return 2

    queries = build_queries(
        base_query=args.query,
        domain_topics=domain_topics,
        qualifier_topics=qualifier_topics,
        legacy_topics=legacy_topics,
    )

    print(f"Base query: {args.query}")
    print(f"Domain topics: {domain_topics if domain_topics else '[none]'}")
    print(f"Qualifier topics: {qualifier_topics if qualifier_topics else '[none]'}")
    print(f"Legacy topics: {legacy_topics if legacy_topics else '[none]'}")
    print(f"Query count: {len(queries)}")

    all_repos: List[Dict[str, Any]] = []
    repo_topics: Dict[str, Dict[str, Set[Any]]] = {}
    query_failures: List[Dict[str, Any]] = []
    repo_errors: List[Dict[str, Any]] = []
    successful_query_count = 0

    for spec in queries:
        print(f"\n[QUERY] {spec.query}")
        try:
            repos = search_repositories(
                token=args.token,
                query=spec.query,
                max_repos=args.max_repos,
            )
        except Exception as exc:
            error_summary = summarize_request_error(exc)
            print(f"[QUERY ERROR] {error_summary}", file=sys.stderr)
            query_failures.append(
                {
                    "query": spec.query,
                    "domain_topic": spec.domain_topic,
                    "qualifier_topic": spec.qualifier_topic,
                    "legacy_topic": spec.legacy_topic,
                    "error": error_summary,
                }
            )
            continue

        successful_query_count += 1
        print(f"[QUERY RESULT] {len(repos)} repos")

        for repo in repos:
            full_name = repo.get("full_name")
            if not full_name:
                continue
            state = repo_topics.setdefault(full_name, empty_repo_topic_state())
            if spec.domain_topic:
                state["domains"].add(spec.domain_topic)
            if spec.qualifier_topic:
                state["qualifiers"].add(spec.qualifier_topic)
            if spec.domain_topic and spec.qualifier_topic:
                state["pairs"].add((spec.domain_topic, spec.qualifier_topic))
            if spec.legacy_topic:
                state["legacy_topics"].add(spec.legacy_topic)

        all_repos.extend(repos)

    repos = dedupe_repos(all_repos)
    print(f"\nUnique candidate repos: {len(repos)}")

    report: List[Dict[str, Any]] = []

    for repo in repos:
        full_name = repo["full_name"]
        print(f"\n=== Checking {full_name} ===")

        if already_added(sciskill_root, full_name):
            print("Already added")
            report.append(
                {
                    "repo": full_name,
                    **build_repo_topic_payload(repo_topics.get(full_name)),
                    "status": "already_added",
                    "target_path": str(submodule_target_path(sciskill_root, full_name)),
                    "matches": [],
                }
            )
            continue

        try:
            matches = find_valid_skill_in_repo(args.token, full_name)
        except Exception as e:
            print(f"[WARN] failed checking {full_name}: {e}", file=sys.stderr)
            report.append(
                {
                    "repo": full_name,
                    **build_repo_topic_payload(repo_topics.get(full_name)),
                    "status": "error",
                }
            )
            repo_errors.append(
                {
                    "repo": full_name,
                    **build_repo_topic_payload(repo_topics.get(full_name)),
                    "status": "error",
                    "error": str(e),
                }
            )
            continue

        if not matches:
            print("No valid SKILL.md found")
            report.append(
                {
                    "repo": full_name,
                    **build_repo_topic_payload(repo_topics.get(full_name)),
                    "status": "no_valid_skill",
                }
            )
            continue

        chosen = matches[0]

        try:
            clone_url = clone_skill_repo(
                sciskill_root=sciskill_root,
                full_name=full_name,
                default_branch=chosen.default_branch,
                dry_run=args.dry_run,
            )

            if not args.dry_run:
                add_to_manifest(sciskill_root, {
                    "fullName": full_name,
                    "cloneUrl": clone_url,
                    "localPath": str(Path("open-source") / full_name),
                    "defaultBranch": chosen.default_branch,
                    "upstreamUrl": chosen.repo_html_url,
                    "addedAt": datetime.utcnow().isoformat() + "Z",
                    "addedBy": "github-actions",
                })

            status = "would_add" if args.dry_run else "added"
            report.append(
                {
                    "repo": full_name,
                    **build_repo_topic_payload(repo_topics.get(full_name)),
                    "status": status,
                    "clone_url": clone_url,
                    "chosen_skill_path": chosen.skill_path,
                    "front_matter": chosen.front_matter,
                    "html_url": chosen.repo_html_url,
                    "target_path": str(submodule_target_path(sciskill_root, full_name)),
                }
            )
        except Exception as e:
            print(f"[WARN] clone failed for {full_name}: {e}", file=sys.stderr)
            entry = {
                "repo": full_name,
                **build_repo_topic_payload(repo_topics.get(full_name)),
                "status": "add_failed",
                "chosen_skill_path": chosen.skill_path,
                "front_matter": chosen.front_matter,
                "html_url": chosen.repo_html_url,
            }
            report.append(entry)
            error_entry = {
                "repo": full_name,
                **build_repo_topic_payload(repo_topics.get(full_name)),
                "status": "add_failed",
                "error": str(e),
                "chosen_skill_path": chosen.skill_path,
                "front_matter": chosen.front_matter,
                "html_url": chosen.repo_html_url,
            }
            if isinstance(e, CloneError):
                error_entry["clone_attempts"] = e.attempts
            repo_errors.append(error_entry)

        time.sleep(0.3)

    report_arg_path = Path(args.report)
    error_report_arg_path = Path(args.error_report) if args.error_report else default_error_report_path(report_arg_path)
    report_path = report_arg_path.resolve()
    error_report_path = error_report_arg_path.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    error_report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            make_json_safe(
                {
                "base_query": args.query,
                "domain_topics": domain_topics,
                "qualifier_topics": qualifier_topics,
                "legacy_topics": legacy_topics,
                "query_count": len(queries),
                "successful_query_count": successful_query_count,
                "query_failure_count": len(query_failures),
                "repo_error_count": len(repo_errors),
                "error_report": str(error_report_arg_path),
                "repo_count": len(repos),
                "results": report,
                }
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    error_report_path.write_text(
        json.dumps(
            make_json_safe(
                {
                    "base_query": args.query,
                    "domain_topics": domain_topics,
                    "qualifier_topics": qualifier_topics,
                    "legacy_topics": legacy_topics,
                    "query_count": len(queries),
                    "successful_query_count": successful_query_count,
                    "report": str(report_arg_path),
                    "query_failures": query_failures,
                    "repo_error_count": len(repo_errors),
                    "repo_errors": repo_errors,
                }
            ),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nReport saved to: {report_path}")
    print(f"Error report saved to: {error_report_path}")
    repair_manifest(sciskill_root)
    if not args.dry_run:
        generate_registry_markdown(sciskill_root)
    if queries and successful_query_count == 0:
        print("ERROR: all GitHub search queries failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
