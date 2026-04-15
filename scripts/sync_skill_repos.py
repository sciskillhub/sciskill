#!/usr/bin/env python3
"""
根据 skill-manifest.json 同步 sciskill 仓库下的 skill 子仓库。

用法:
    # 同步主仓库 + 所有 skill 子仓库；有变更时自动 add/commit/push
    python3 scripts/sync_skill_repos.py --dest .

    # 只同步子仓库（跳过主仓库 pull）
    python3 scripts/sync_skill_repos.py --dest . --skip-pull

    # 只同步指定的子仓库
    python3 scripts/sync_skill_repos.py --dest . --only owner/repo

    # 仅同步，不自动提交或推送
    python3 scripts/sync_skill_repos.py --dest . --no-auto-commit

依赖: 无（纯标准库）
"""

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

MANIFEST_FILENAME = "skill-manifest.json"
GIT_TIMEOUT = 300


def git_auth_args(token):
    if not token:
        return []
    encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode("ascii")
    return ["-c", f"http.https://github.com/.extraheader=AUTHORIZATION: basic {encoded}"]


def run_git(args, cwd=None, check=True, timeout=GIT_TIMEOUT):
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr}")
    return result


def repo_has_relevant_changes(repo_root):
    result = run_git(
        ["git", "status", "--porcelain", "--", MANIFEST_FILENAME, "open-source"],
        cwd=repo_root,
        check=False,
    )
    return bool((result.stdout or "").strip())


def current_branch(repo_root):
    return run_git(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        check=False,
    ).stdout.strip()


def auto_commit_and_push(repo_root, auto_push=True):
    if not repo_has_relevant_changes(repo_root):
        print("[3/3] No manifest or skill repo changes to commit")
        return True

    print("[3/3] Auto-committing synced changes...")
    run_git(["git", "add", MANIFEST_FILENAME, "open-source"], cwd=repo_root)

    commit_result = run_git(
        ["git", "commit", "-m", "chore: sync skill repos"],
        cwd=repo_root,
        check=False,
    )
    if commit_result.returncode != 0:
        output = (commit_result.stderr or commit_result.stdout or "").strip()
        if "nothing to commit" in output.lower():
            print("[OK] nothing to commit after staging")
            return True
        print(f"[ERROR] auto-commit failed: {output}")
        return False

    print("[OK] committed synced changes")
    if not auto_push:
        print("[INFO] auto-push disabled")
        return True

    branch = current_branch(repo_root)
    if not branch:
        print("[ERROR] could not detect current branch for push")
        return False

    print(f"[4/4] Pushing to origin/{branch}...")
    push_result = run_git(["git", "push", "origin", branch], cwd=repo_root, check=False)
    if push_result.returncode != 0:
        output = (push_result.stderr or push_result.stdout or "").strip()
        print(f"[ERROR] auto-push failed: {output}")
        return False

    print("[OK] pushed synced changes")
    return True


def load_manifest(repo_root):
    mp = Path(repo_root) / MANIFEST_FILENAME
    if not mp.is_file():
        print(f"[WARN] {mp} not found")
        return []
    try:
        return json.loads(mp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"[ERROR] Failed to parse manifest: {e}")
        return []


def repair_manifest(repo_root):
    script_path = Path(__file__).with_name("repair_skill_manifest.py")
    if not script_path.is_file():
        return False
    result = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(repo_root)],
        cwd=repo_root,
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
        print(f"[WARN] manifest repair failed: {error}")
    return False


def inject_token(url, token):
    if token and url.startswith("https://github.com/"):
        return url.replace("https://", f"https://{token}@", 1)
    return url


def _update_manifest_branch(repo_root, full_name, branch):
    """Update defaultBranch in manifest when the recorded value was wrong."""
    mp = Path(repo_root) / MANIFEST_FILENAME
    try:
        entries = json.loads(mp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    for entry in entries:
        if entry.get("fullName") == full_name:
            entry["defaultBranch"] = branch
            break
    mp.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _update_manifest_sha(repo_root, full_name, sha):
    """Update lastCommitSha in manifest when the commit actually changed."""
    mp = Path(repo_root) / MANIFEST_FILENAME
    try:
        entries = json.loads(mp.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return
    for entry in entries:
        if entry.get("fullName") == full_name:
            entry["lastCommitSha"] = sha
            break
    mp.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sync_manifest_after_clone(repo_root, entry, local_path, recorded_branch):
    """After a fresh clone, update lastCommitSha and defaultBranch in manifest if they differ."""
    new_sha = run_git(["git", "rev-parse", "HEAD"], cwd=local_path, check=False).stdout.strip()
    if not new_sha:
        return
    old_sha = entry.get("lastCommitSha", "")
    if new_sha != old_sha:
        _update_manifest_sha(repo_root, entry.get("fullName", ""), new_sha)

    # Detect actual branch and correct manifest if needed
    head_branch = run_git(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=local_path, check=False,
    ).stdout.strip()
    if head_branch and head_branch != recorded_branch:
        _update_manifest_branch(repo_root, entry.get("fullName", ""), head_branch)


def sync_skill_repo(repo_root, entry, token):
    local_path = Path(repo_root) / entry["localPath"]
    clone_url = inject_token(entry.get("cloneUrl", ""), token)
    branch = entry.get("defaultBranch", "main")
    full_name = entry.get("fullName", "?")

    # Update existing repo
    if local_path.exists() and (local_path / ".git").exists():
        print(f"  [update] {full_name}", end=" ", flush=True)
        auth = git_auth_args(token)
        try:
            old_sha = run_git(["git", "rev-parse", "HEAD"], cwd=local_path, check=False).stdout.strip()

            result = run_git(["git"] + auth + ["fetch", "origin", branch], cwd=local_path, check=False)
            if result.returncode == 0:
                effective_branch = branch
            else:
                # Branch name in manifest may be wrong — fetch all and detect actual default branch
                run_git(["git"] + auth + ["fetch", "origin"], cwd=local_path)
                head_branch = run_git(
                    ["git", "rev-parse", "--abbrev-ref", "refs/remotes/origin/HEAD"],
                    cwd=local_path, check=False,
                )
                effective_branch = (head_branch.stdout or "").strip()
                if effective_branch.startswith("origin/"):
                    effective_branch = effective_branch[len("origin/"):]
                else:
                    branches = run_git(["git", "branch", "-r"], cwd=local_path, check=False)
                    first = (branches.stdout or "").strip().splitlines()
                    effective_branch = first[0].strip().replace("origin/", "").split()[0] if first else branch
                print(f"(branch {branch}->{effective_branch}) ", end="", flush=True)

            run_git(["git", "reset", "--hard", f"origin/{effective_branch}"], cwd=local_path)
            new_sha = run_git(["git", "rev-parse", "HEAD"], cwd=local_path, check=False).stdout.strip()

            # Update manifest if branch was corrected
            if effective_branch != branch:
                _update_manifest_branch(repo_root, full_name, effective_branch)

            # Only update lastCommitSha when commit actually changed
            if new_sha and new_sha != old_sha:
                _update_manifest_sha(repo_root, full_name, new_sha)
                print("OK (updated)")
            else:
                print("OK (no change)")
            return True
        except Exception as e:
            print(f"FAILED ({e})")
            return False

    # Clone fresh
    if local_path.exists():
        shutil.rmtree(local_path, ignore_errors=True)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  [clone] {full_name}", end=" ", flush=True)

    # Try with --branch first
    auth = git_auth_args(token)
    result = run_git(
        ["git"] + auth + ["clone", "--depth", "1", "--branch", branch, clone_url, str(local_path)],
        cwd=local_path.parent, check=False,
    )
    if result.returncode == 0:
        _sync_manifest_after_clone(repo_root, entry, local_path, branch)
        print("OK")
        return True

    # Retry without --branch
    shutil.rmtree(local_path, ignore_errors=True)
    result = run_git(
        ["git"] + auth + ["clone", "--depth", "1", clone_url, str(local_path)],
        cwd=local_path.parent, check=False,
    )
    if result.returncode == 0:
        _sync_manifest_after_clone(repo_root, entry, local_path, branch)
        print("OK")
        return True

    shutil.rmtree(local_path, ignore_errors=True)
    stderr = result.stderr.strip()[:80]
    print(f"FAILED ({stderr})")
    return False


def main():
    parser = argparse.ArgumentParser(description="Sync skill repos from skill-manifest.json")
    parser.add_argument("--dest", default=".", help="sciskill repo root directory")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""), help="GitHub token")
    parser.add_argument("--skip-pull", action="store_true", help="Skip git pull on main repo")
    parser.add_argument("--only", action="append", help="Only sync specific fullName (can repeat)")
    parser.add_argument("--no-auto-commit", action="store_true", help="Do not auto add/commit synced changes")
    parser.add_argument("--no-auto-push", action="store_true", help="Do not auto push after auto-commit")
    args = parser.parse_args()

    repo_root = Path(args.dest).resolve()
    token = args.token.strip()

    if not (repo_root / ".git").exists():
        print(f"[ERROR] {repo_root} is not a git repository")
        return 1

    # Pull main repo
    if not args.skip_pull:
        print("[1/2] Pulling main repo...")
        auth = git_auth_args(token)
        run_git(["git"] + auth + ["pull"], cwd=repo_root, check=False)
    else:
        print("[1/2] Skipping main repo pull")

    repair_manifest(repo_root)
    # Load manifest
    manifest = load_manifest(repo_root)
    if not manifest:
        print("[ERROR] No manifest entries found")
        return 1

    # Filter if --only
    if args.only:
        only_set = set(args.only)
        manifest = [e for e in manifest if e.get("fullName") in only_set]
        if not manifest:
            print(f"[ERROR] None of --only entries found in manifest: {only_set}")
            return 1

    # Sync skill repos
    print(f"[2/2] Syncing {len(manifest)} skill repos...")
    success = 0
    failed = []
    for entry in manifest:
        if sync_skill_repo(repo_root, entry, token):
            success += 1
        else:
            failed.append(entry.get("fullName", "?"))

    print(f"\nDone: {success}/{len(manifest)} OK")
    if failed:
        print(f"Failed ({len(failed)}):")
        for name in failed:
            print(f"  - {name}")
        return 1
    if not args.no_auto_commit:
        return 0 if auto_commit_and_push(repo_root, auto_push=not args.no_auto_push) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
