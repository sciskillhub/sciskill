#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

MANIFEST_FILENAME = "skill-manifest.json"
CONFLICT_START = "<<<<<<< HEAD"
CONFLICT_MID = "======="
CONFLICT_END_PREFIX = ">>>>>>>"


def manifest_path(repo_root: Path) -> Path:
    return repo_root / MANIFEST_FILENAME


def external_manifest_path(repo_root: Path) -> Path:
    configured = os.environ.get("SCISKILL_DATA_DIR", "").strip()
    data_root = Path(configured).expanduser().resolve() if configured else (repo_root.parent / "data").resolve()
    return data_root / MANIFEST_FILENAME


def resolve_last_commit_conflicts(raw_text: str) -> Tuple[str, int]:
    lines = raw_text.splitlines()
    resolved_lines: List[str] = []
    resolved_count = 0
    index = 0

    while index < len(lines):
        line = lines[index]
        if line == CONFLICT_START:
            if index + 4 >= len(lines):
                raise ValueError(f"incomplete merge conflict near line {index + 1}")

            head_line = lines[index + 1]
            mid_line = lines[index + 2]
            their_line = lines[index + 3]
            end_line = lines[index + 4]

            head_match = re.match(r'(\s*)"lastCommitSha":\s*"([0-9a-f]{7,64})",\s*$', head_line)
            their_match = re.match(r'(\s*)"lastCommitSha":\s*"([0-9a-f]{7,64})",\s*$', their_line)
            if (
                mid_line != CONFLICT_MID
                or not end_line.startswith(CONFLICT_END_PREFIX)
                or not head_match
                or not their_match
            ):
                raise ValueError(
                    "unsupported merge conflict shape in skill-manifest.json; "
                    "expected a lastCommitSha-only conflict block"
                )

            resolved_count += 1
            index += 5
            continue

        resolved_lines.append(line)
        index += 1

    text = "\n".join(resolved_lines)
    if raw_text.endswith("\n"):
        text += "\n"
    return text, resolved_count


def strip_manifest_commit_shas(entries: List[Dict[str, Any]]) -> int:
    removed = 0
    for entry in entries:
        if "lastCommitSha" in entry:
            del entry["lastCommitSha"]
            removed += 1
    return removed


def write_manifest_atomically(target: Path, entries: List[Dict[str, Any]]) -> None:
    payload = json.dumps(sorted(entries, key=lambda item: item.get("fullName", "")), indent=2, ensure_ascii=False) + "\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".skill-manifest-", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        Path(temp_path).replace(target)
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except OSError:
            pass


def write_manifest_and_mirror(repo_root: Path, entries: List[Dict[str, Any]]) -> None:
    primary = manifest_path(repo_root)
    write_manifest_atomically(primary, entries)
    mirror = external_manifest_path(repo_root)
    if mirror.resolve() != primary.resolve():
        write_manifest_atomically(mirror, entries)


def repair_manifest(repo_root: Path) -> Tuple[int, int, int]:
    target = manifest_path(repo_root)
    if not target.is_file():
        raise FileNotFoundError(f"manifest not found: {target}")

    raw_text = target.read_text(encoding="utf-8")
    cleaned_text, resolved_conflicts = resolve_last_commit_conflicts(raw_text)
    entries = json.loads(cleaned_text)
    if not isinstance(entries, list):
        raise ValueError("manifest root must be a JSON array")

    removed_shas = strip_manifest_commit_shas(entries)
    write_manifest_and_mirror(repo_root, entries)
    return len(entries), resolved_conflicts, removed_shas


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair skill-manifest.json conflicts and remove legacy lastCommitSha fields.")
    parser.add_argument("--repo-root", default=".", help="Path to the sciskill repo root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / ".git").exists():
        print(f"[ERROR] not a git repository: {repo_root}", file=sys.stderr)
        return 2

    try:
        entry_count, resolved_conflicts, removed_shas = repair_manifest(repo_root)
    except Exception as exc:
        print(f"[ERROR] failed to repair {manifest_path(repo_root)}: {exc}", file=sys.stderr)
        return 1

    print(
        f"[OK] repaired {manifest_path(repo_root)} "
        f"(entries={entry_count}, resolved_conflicts={resolved_conflicts}, removed_shas={removed_shas})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
