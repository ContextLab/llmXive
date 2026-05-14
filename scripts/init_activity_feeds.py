#!/usr/bin/env python3
"""T079 (spec 009): one-time backfill of activity.jsonl for existing projects.

Creates an empty activity.jsonl at projects/PROJ-*/activity.jsonl for every
project that doesn't already have one. Idempotent — skips projects whose
feed already exists.

Usage:
    python scripts/init_activity_feeds.py                  # backfill all
    python scripts/init_activity_feeds.py --dry-run        # report only

Constitution V: fail-fast on missing projects/ directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Initialize activity feeds for existing projects.")
    parser.add_argument("--repo-root", default=".", help="Repo root (default: cwd)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing")
    args = parser.parse_args(argv)

    repo = Path(args.repo_root).resolve()
    projects_dir = repo / "projects"
    if not projects_dir.is_dir():
        print(f"FATAL: projects directory not found: {projects_dir}", file=sys.stderr)
        return 2

    projects = [p for p in projects_dir.iterdir() if p.is_dir() and p.name.startswith("PROJ-")]
    created = 0
    skipped = 0
    for proj in sorted(projects):
        feed = proj / "activity.jsonl"
        if feed.exists():
            skipped += 1
            continue
        if args.dry_run:
            print(f"would create: {feed.relative_to(repo)}")
            created += 1
            continue
        feed.touch()
        print(f"created: {feed.relative_to(repo)}")
        created += 1

    print(f"\nSummary: {created} created, {skipped} already existed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
