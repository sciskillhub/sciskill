#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

MANIFEST_FILENAME = "skill-manifest.json"
CONFLICT_START = "<<<<<<< HEAD"
CONFLICT_MID = "======="
CONFLICT_END_PREFIX = ">>>>>>>"


def manifest_path(repo_root: Path) -> Path:
    return repo_root / MANIFEST_FILENAME


def repo_head_sha(repo_path: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    value = (result.stdout or "").strip()
    return value or None


def resolve_last_commit_conflicts(repo_root: Path, raw_text: str) -> Tuple[str, int]:
    lines = raw_text.splitlines()
    resolved_lines: List[str] = []
    current_local_path: Optional[str] = None
    resolved_count = 0
    index = 0

    while index < len(lines):
        line = lines[index]
        local_path_match = re.match(r'\s*"localPath":\s*"([^"]+)"', line)
        if local_path_match:
            current_local_path = local_path_match.group(1)

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

            chosen_sha = head_match.group(2)
            if current_local_path:
                actual_sha = repo_head_sha(repo_root / current_local_path)
                if actual_sha:
                    chosen_sha = actual_sha

            resolved_lines.append(f'{head_match.group(1)}"lastCommitSha": "{chosen_sha}",')
            resolved_count += 1
            index += 5
            continue

        resolved_lines.append(line)
        index += 1

    text = "\n".join(resolved_lines)
    if raw_text.endswith("\n"):
        text += "\n"
    return text, resolved_count


def update_manifest_shas(repo_root: Path, entries: List[Dict[str, Any]]) -> int:
    updated = 0
    for entry in entries:
        local_path = str(entry.get("localPath") or "").strip()
        if not local_path:
            continue
        actual_sha = repo_head_sha(repo_root / local_path)
        if actual_sha and entry.get("lastCommitSha") != actual_sha:
            entry["lastCommitSha"] = actual_sha
            updated += 1
    return updated


def write_manifest_atomically(target: Path, entries: List[Dict[str, Any]]) -> None:
    payload = json.dumps(sorted(entries, key=lambda item: item.get("fullName", "")), indent=2, ensure_ascii=False) + "\n"
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


def repair_manifest(repo_root: Path) -> Tuple[int, int, int]:
    target = manifest_path(repo_root)
    if not target.is_file():
        raise FileNotFoundError(f"manifest not found: {target}")

    raw_text = target.read_text(encoding="utf-8")
    cleaned_text, resolved_conflicts = resolve_last_commit_conflicts(repo_root, raw_text)
    entries = json.loads(cleaned_text)
    if not isinstance(entries, list):
        raise ValueError("manifest root must be a JSON array")

    updated_shas = update_manifest_shas(repo_root, entries)
    write_manifest_atomically(target, entries)
    return len(entries), resolved_conflicts, updated_shas


def main() -> int:
    parser = argparse.ArgumentParser(description="Repair skill-manifest.json conflicts and refresh lastCommitSha from local repos.")
    parser.add_argument("--repo-root", default=".", help="Path to the sciskill repo root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / ".git").exists():
        print(f"[ERROR] not a git repository: {repo_root}", file=sys.stderr)
        return 2

    try:
        entry_count, resolved_conflicts, updated_shas = repair_manifest(repo_root)
    except Exception as exc:
        print(f"[ERROR] failed to repair {manifest_path(repo_root)}: {exc}", file=sys.stderr)
        return 1

    print(
        f"[OK] repaired {manifest_path(repo_root)} "
        f"(entries={entry_count}, resolved_conflicts={resolved_conflicts}, updated_shas={updated_shas})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
