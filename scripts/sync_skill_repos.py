#!/usr/bin/env python3
"""
Sync skill repositories listed in skill-manifest.json into an external cache root.

This script intentionally does not mutate the sciskill git worktree. The sciskill
repository acts as a registry only; live repository contents are stored under an
external cache root, which defaults to ../data relative to the repo root.

Examples:
    python3 scripts/sync_skill_repos.py --dest .
    python3 scripts/sync_skill_repos.py --dest . --cache-root ../data/open-source
    python3 scripts/sync_skill_repos.py --dest . --only owner/repo
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

MANIFEST_FILENAME = "skill-manifest.json"
GIT_TIMEOUT = 300


def git_auth_args(token: str) -> list[str]:
    if not token:
        return []
    encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode("ascii")
    return ["-c", f"http.https://github.com/.extraheader=AUTHORIZATION: basic {encoded}"]


def run_git(args: list[str], cwd: Path | None = None, check: bool = True, timeout: int = GIT_TIMEOUT) -> subprocess.CompletedProcess:
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return result


def current_branch(repo_root: Path) -> str:
    return run_git(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        check=False,
    ).stdout.strip()


def ensure_clean_main_repo(repo_root: Path) -> None:
    result = run_git(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=repo_root,
        check=False,
    )
    if (result.stdout or "").strip():
        raise RuntimeError(
            "main repo has local tracked changes; refuse to sync automatically. "
            "Commit/stash/reset changes first."
        )


def sync_main_repo_fast_forward(repo_root: Path, token: str) -> str:
    branch = current_branch(repo_root)
    if not branch:
        raise RuntimeError("could not detect current branch for main repo sync")

    ensure_clean_main_repo(repo_root)
    auth = git_auth_args(token)
    print(f"[1/3] Fetching origin/{branch} for fast-forward sync...")
    run_git(["git"] + auth + ["fetch", "origin", branch], cwd=repo_root)

    counts = run_git(
        ["git", "rev-list", "--left-right", "--count", f"HEAD...refs/remotes/origin/{branch}"],
        cwd=repo_root,
        check=False,
    ).stdout.strip()
    try:
        ahead, behind = (int(part) for part in counts.split())
    except Exception as exc:
        raise RuntimeError(f"failed to parse main repo divergence state: {counts}") from exc

    if ahead and behind:
        raise RuntimeError(
            f"main repo has diverged from origin/{branch} (local-only={ahead}, remote-only={behind}); "
            "refuse to merge automatically. Rebase or reset explicitly."
        )
    if ahead:
        raise RuntimeError(
            f"main repo has {ahead} local-only commit(s) on {branch}; "
            "refuse to overwrite or merge automatically."
        )
    if behind:
        print(f"[1/3] Fast-forwarding {branch} by {behind} commit(s)...")
        run_git(["git", "merge", "--ff-only", f"refs/remotes/origin/{branch}"], cwd=repo_root)
    else:
        print(f"[1/3] Main repo already matches origin/{branch}")

    return branch


def load_manifest(repo_root: Path) -> list[dict]:
    manifest_path = repo_root / MANIFEST_FILENAME
    if not manifest_path.is_file():
        print(f"[WARN] {manifest_path} not found")
        return []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[ERROR] Failed to parse {MANIFEST_FILENAME}: {exc}")
        return []
    return payload if isinstance(payload, list) else []


def inject_token(url: str, token: str) -> str:
    if token and url.startswith("https://github.com/"):
        return url.replace("https://", f"https://{token}@", 1)
    return url


def cache_relative_path(local_path: str) -> Path:
    raw = Path(local_path)
    parts = raw.parts
    if parts and parts[0] == "open-source":
        parts = parts[1:]
    return Path(*parts) if parts else Path()


def determine_remote_branch(repo_path: Path, recorded_branch: str) -> str:
    fetch_recorded = run_git(
        ["git", "fetch", "origin", recorded_branch],
        cwd=repo_path,
        check=False,
    )
    if fetch_recorded.returncode == 0:
        return recorded_branch

    fetch_all = run_git(["git", "fetch", "origin"], cwd=repo_path, check=False)
    if fetch_all.returncode != 0:
        raise RuntimeError(fetch_all.stderr.strip() or fetch_all.stdout.strip() or "fetch origin failed")

    remote_head = run_git(
        ["git", "rev-parse", "--abbrev-ref", "refs/remotes/origin/HEAD"],
        cwd=repo_path,
        check=False,
    ).stdout.strip()
    if remote_head.startswith("origin/"):
        return remote_head[len("origin/"):]

    remote_branches = run_git(
        ["git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"],
        cwd=repo_path,
        check=False,
    ).stdout.splitlines()
    for branch in remote_branches:
        branch = branch.strip()
        if branch.startswith("origin/") and branch != "origin/HEAD":
            return branch[len("origin/"):]

    return recorded_branch


def clone_or_update_repo(cache_root: Path, entry: dict, token: str) -> bool:
    full_name = str(entry.get("fullName") or "?")
    local_path = str(entry.get("localPath") or "").strip()
    clone_url = inject_token(str(entry.get("cloneUrl") or "").strip(), token)
    branch = str(entry.get("defaultBranch") or "main").strip() or "main"

    if not local_path:
        print(f"  [skip] {full_name} missing localPath in manifest")
        return False
    if not clone_url:
        print(f"  [skip] {full_name} missing cloneUrl in manifest")
        return False

    target_path = (cache_root / cache_relative_path(local_path)).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if (target_path / ".git").exists():
        print(f"  [update] {full_name}", end=" ", flush=True)
        try:
            effective_branch = determine_remote_branch(target_path, branch)
            run_git(["git", "checkout", "--force", "-B", effective_branch, f"origin/{effective_branch}"], cwd=target_path)
            run_git(["git", "reset", "--hard", f"origin/{effective_branch}"], cwd=target_path)
            print(f"OK ({effective_branch})")
            return True
        except Exception as exc:
            print(f"FAILED ({exc})")
            return False

    if target_path.exists():
        print(f"  [replace] {full_name} existing non-git path -> reclone")
        if target_path.is_dir():
            shutil.rmtree(target_path, ignore_errors=True)
        else:
            target_path.unlink(missing_ok=True)

    print(f"  [clone] {full_name}", end=" ", flush=True)
    auth = git_auth_args(token)
    result = run_git(
        ["git"] + auth + ["clone", "--depth", "1", "--branch", branch, clone_url, str(target_path)],
        cwd=cache_root,
        check=False,
    )
    if result.returncode == 0:
        print("OK")
        return True

    if target_path.exists():
        if target_path.is_dir():
            shutil.rmtree(target_path, ignore_errors=True)
        else:
            target_path.unlink(missing_ok=True)

    fallback = run_git(
        ["git"] + auth + ["clone", "--depth", "1", clone_url, str(target_path)],
        cwd=cache_root,
        check=False,
    )
    if fallback.returncode == 0:
        print("OK (fallback)")
        return True

    error = (fallback.stderr or fallback.stdout or result.stderr or result.stdout).strip()
    print(f"FAILED ({error})")
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync skill repos from skill-manifest.json into an external cache")
    parser.add_argument("--dest", default=".", help="sciskill repo root directory")
    parser.add_argument(
        "--cache-root",
        default="",
        help="external cache root. Defaults to ../data/open-source relative to the sciskill repo root",
    )
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""), help="GitHub token")
    parser.add_argument("--skip-pull", action="store_true", help="Skip fast-forward sync on main repo")
    parser.add_argument("--only", action="append", help="Only sync specific fullName (can repeat)")
    parser.add_argument("--auto-commit", action="store_true", help="Deprecated; registry-only mode never commits")
    parser.add_argument("--auto-push", action="store_true", help="Deprecated; registry-only mode never pushes")
    parser.add_argument("--no-auto-commit", action="store_true", help="Deprecated compatibility flag")
    parser.add_argument("--no-auto-push", action="store_true", help="Deprecated compatibility flag")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.dest).resolve()
    token = args.token.strip()
    cache_root = Path(args.cache_root).resolve() if args.cache_root else (repo_root.parent / "data" / "open-source").resolve()

    if not (repo_root / ".git").exists():
        print(f"[ERROR] {repo_root} is not a git repository")
        return 1

    if args.auto_commit or args.auto_push or args.no_auto_commit or args.no_auto_push:
        print("[WARN] auto-commit/push flags are ignored in registry-only mode")

    if not args.skip_pull:
        try:
            sync_main_repo_fast_forward(repo_root, token)
        except Exception as exc:
            print(f"[ERROR] Failed to fast-forward main repo: {exc}")
            return 1
    else:
        print("[1/3] Skipping main repo fast-forward sync")

    manifest = load_manifest(repo_root)
    if not manifest:
        print("[ERROR] No manifest entries found")
        return 1

    if args.only:
        only_set = set(args.only)
        manifest = [entry for entry in manifest if entry.get("fullName") in only_set]
        if not manifest:
            print(f"[ERROR] None of --only entries found in manifest: {only_set}")
            return 1

    cache_root.mkdir(parents=True, exist_ok=True)
    print(f"[2/3] External cache root: {cache_root}")
    print(f"[3/3] Syncing {len(manifest)} skill repos into cache...")

    success = 0
    failed: list[str] = []
    for entry in manifest:
        if clone_or_update_repo(cache_root, entry, token):
            success += 1
        else:
            failed.append(str(entry.get("fullName") or "?"))

    print(f"\nDone: {success}/{len(manifest)} OK")
    if failed:
        print(f"Failed ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")
        return 1

    print("[INFO] Registry repo left untouched; no commit or push performed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
