#!/usr/bin/env python3
"""SessionStart hook: where the session is and what the guard refuses, in
three lines at most. Plain stdout joins the model's context. Never fails the session. Python 3.8."""
import json
import os
import subprocess
import sys


def git(cwd, *args):
    try:
        out = subprocess.run(["git", "-C", cwd] + list(args), capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:  # noqa: B902
        return ""


def refuses():
    """The guard's own list (guard.REFUSES), so this line cannot drift from the code."""
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import guard
        return list(guard.REFUSES)
    except Exception:  # noqa: B902
        return ["see .claude/hooks/guard.py"]


def compose(cwd, branch, behind, changed):
    """The lines printed at start. Pure."""
    lines = ["docket: %s on branch %s." % (cwd, branch)]
    if branch == "master":
        lines.append("On master: make a branch (or a worktree) before you change anything.")
    elif behind and behind != "0":
        lines.append("This branch is %s commits behind origin/master." % behind)
    if changed:
        lines.append("Uncommitted changes: %d files." % changed)
    lines.append("The guard refuses: %s. `tools/dk/dk why --list` has every check." % ", ".join(refuses()))
    return lines


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: B902
        data = {}
    cwd = data.get("cwd") or os.getcwd()
    branch = git(cwd, "rev-parse", "--abbrev-ref", "HEAD") or "(detached HEAD)"
    behind = "0" if branch == "master" else git(cwd, "rev-list", "--count", "HEAD..origin/master")
    changed = git(cwd, "status", "--porcelain")
    print("\n".join(compose(cwd, branch, behind, len(changed.splitlines()) if changed else 0)))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: B902
        pass
    sys.exit(0)
