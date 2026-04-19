#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

MANIFEST_FILENAME = "skill-manifest.json"
REPORT_FILENAME = "reports/skill_report.json"
DEFAULT_OUTPUT_FILENAME = "open-source-skills.md"


def load_json(path: Path):
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(repo_root: Path) -> list[dict]:
    payload = load_json(repo_root / MANIFEST_FILENAME)
    return payload if isinstance(payload, list) else []


def load_report_map(repo_root: Path) -> dict[str, dict]:
    payload = load_json(repo_root / REPORT_FILENAME)
    if not isinstance(payload, dict):
        return {}
    results = payload.get("results")
    if not isinstance(results, list):
        return {}
    mapping: dict[str, dict] = {}
    for item in results:
        if isinstance(item, dict) and item.get("repo"):
            mapping[str(item["repo"])] = item
    return mapping


def cache_relative_path(local_path: str) -> Path:
    raw = Path(local_path)
    parts = raw.parts
    if parts and parts[0] == "open-source":
        parts = parts[1:]
    return Path(*parts) if parts else Path()


def parse_frontmatter_description(skill_path: Path) -> tuple[str | None, str | None]:
    try:
        text = skill_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None, None

    if not text.startswith("---"):
        return None, None

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, None

    name = None
    description = None
    index = 1
    while index < len(lines):
        line = lines[index]
        if line.strip() == "---":
            break
        if ":" not in line:
            index += 1
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        raw_value = value.strip()

        if key == "name":
            parsed = raw_value.strip("\"' ")
            if parsed:
                name = parsed
        elif key == "description":
            if raw_value in {"|", ">"}:
                block_lines: list[str] = []
                index += 1
                while index < len(lines):
                    block_line = lines[index]
                    if block_line.strip() == "---":
                        index -= 1
                        break
                    if block_line and not block_line[0].isspace():
                        index -= 1
                        break
                    block_lines.append(block_line.strip())
                    index += 1
                parsed = " ".join(part for part in block_lines if part).strip()
            else:
                parsed = raw_value.strip("\"' ")
            if parsed:
                description = parsed
        index += 1

    return name, description


def find_repo_description(cache_root: Path, local_path: str) -> tuple[str | None, str | None]:
    repo_dir = cache_root / cache_relative_path(local_path)
    if not repo_dir.is_dir():
        return None, None

    for skill_md in sorted(repo_dir.rglob("SKILL.md")):
        skill_name, description = parse_frontmatter_description(skill_md)
        rel_path = skill_md.relative_to(repo_dir).as_posix()
        if description:
            return description, rel_path
        if skill_name:
            return f"Skill repository containing `{skill_name}` and related workflows.", rel_path

    return None, None


def normalize_description(text: str | None) -> str:
    if not text:
        return "Collected GitHub skill repository."
    return " ".join(str(text).split())


def build_repo_cards(entries: list[dict], report_map: dict[str, dict], cache_root: Path) -> list[str]:
    cards: list[str] = []
    for entry in sorted(entries, key=lambda item: str(item.get("fullName") or "").lower()):
        full_name = str(entry.get("fullName") or "")
        upstream_url = str(entry.get("upstreamUrl") or f"https://github.com/{full_name}")
        local_path = str(entry.get("localPath") or "")
        report_item = report_map.get(full_name) or {}

        front_matter = report_item.get("front_matter") if isinstance(report_item, dict) else None
        report_description = None
        report_skill_path = None
        if isinstance(front_matter, dict):
            raw_description = front_matter.get("description")
            if isinstance(raw_description, str) and raw_description.strip():
                report_description = raw_description.strip()
        if isinstance(report_item, dict):
            raw_skill_path = report_item.get("chosen_skill_path")
            if isinstance(raw_skill_path, str) and raw_skill_path.strip():
                report_skill_path = raw_skill_path.strip()

        cache_description, cache_skill_path = find_repo_description(cache_root, local_path)
        description = normalize_description(report_description or cache_description)
        example_path = report_skill_path or cache_skill_path

        cards.append(f"### [{full_name}]({upstream_url})")
        cards.append("")
        cards.append(description)
        cards.append("")
        if example_path:
            cards.append(f"Example skill path: `{example_path}`")
            cards.append("")

    return cards


def build_markdown(entries: list[dict], report_map: dict[str, dict], cache_root: Path) -> str:
    lines = [
        "# Open Source Skills",
        "",
        "Collected GitHub repositories that provide reusable skills, workflows, or domain-specific agent capabilities.",
        "",
        f"Total repositories: **{len(entries)}**",
        "",
    ]
    lines.extend(build_repo_cards(entries, report_map, cache_root))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate open-source-skills.md from skill-manifest.json")
    parser.add_argument("--repo-root", default=".", help="sciskill repo root")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_FILENAME, help="output markdown path, relative to repo root by default")
    parser.add_argument(
        "--cache-root",
        default="",
        help="cache root used to inspect synchronized skill contents. Defaults to ../data/open-source",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (repo_root / output_path).resolve()
    cache_root = Path(args.cache_root).resolve() if args.cache_root else (repo_root.parent / "data" / "open-source").resolve()

    entries = load_manifest(repo_root)
    report_map = load_report_map(repo_root)
    markdown = build_markdown(entries, report_map, cache_root)
    output_path.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
