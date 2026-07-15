#!/usr/bin/env python3
"""Archive (or delete) the dead ``resolved_datasets.yaml`` weak-manifest files.

Issue #1139 / D7: the per-project ``projects/**/.specify/memory/resolved_datasets.yaml``
manifest was WRITE-ONLY — one writer (``dataset_resolver.write_manifest``), zero
non-test readers. The planner consumes the resolver's in-process return value, not
the on-disk file. Those manifests are ~84% ``wrong_format`` noise and total ~9.8 MB
across ~676 files. With ``write_manifest`` removed, this script cleans up the
already-committed manifests.

DEFAULT is a DRY-RUN: it only reports the count + total bytes and lists a sample.
Pass ``--apply`` to actually move each manifest under
``state/_archive/resolved_datasets/<project>/resolved_datasets.yaml`` (preserved
for audit), or ``--apply --delete`` to remove them outright.

Usage:
    python scripts/maintenance/archive_weak_manifests.py            # dry-run report
    python scripts/maintenance/archive_weak_manifests.py --apply    # archive
    python scripts/maintenance/archive_weak_manifests.py --apply --delete  # delete
    python scripts/maintenance/archive_weak_manifests.py --repo-root /path/to/repo
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_MANIFEST_NAME = "resolved_datasets.yaml"


def _default_repo_root() -> Path:
    """Repo root via ``llmxive.config.repo_root`` when importable, else this
    file's location (``scripts/maintenance/`` → repo root)."""
    try:
        from llmxive.config import repo_root

        return repo_root()
    except Exception:
        return Path(__file__).resolve().parent.parent.parent


def find_weak_manifests(repo_root: Path) -> list[Path]:
    """Every ``projects/**/.specify/memory/resolved_datasets.yaml`` under repo.

    Uses ``os.walk``-style rglob but note: ``Path.glob('**')`` skips dot-dirs, so
    we anchor on the known ``.specify/memory`` segment explicitly.
    """
    projects = repo_root / "projects"
    if not projects.is_dir():
        return []
    return sorted(projects.glob(f"*/.specify/memory/{_MANIFEST_NAME}"))


def _archive_target(repo_root: Path, manifest: Path) -> Path:
    """``state/_archive/resolved_datasets/<project>/resolved_datasets.yaml``."""
    # projects/<project>/.specify/memory/resolved_datasets.yaml → <project>.
    try:
        rel = manifest.relative_to(repo_root / "projects")
        project = rel.parts[0]
    except (ValueError, IndexError):
        project = manifest.parent.parent.parent.name
    return repo_root / "state" / "_archive" / "resolved_datasets" / project / _MANIFEST_NAME


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", type=Path, default=None,
        help="Repository root (default: llmxive.config.repo_root()).",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually archive/delete (default: dry-run report only).",
    )
    parser.add_argument(
        "--delete", action="store_true",
        help="With --apply, DELETE the manifests instead of archiving them.",
    )
    args = parser.parse_args(argv)

    repo_root = (args.repo_root or _default_repo_root()).resolve()
    manifests = find_weak_manifests(repo_root)
    total_bytes = sum((m.stat().st_size for m in manifests if m.is_file()), 0)

    action = "delete" if args.delete else "archive"
    print(f"repo root: {repo_root}")
    print(f"found {len(manifests)} '{_MANIFEST_NAME}' manifest(s), "
          f"{total_bytes:,} bytes total")
    for m in manifests[:10]:
        print(f"  - {m.relative_to(repo_root)}")
    if len(manifests) > 10:
        print(f"  … and {len(manifests) - 10} more")

    if not manifests:
        return 0

    if not args.apply:
        print(f"\nDRY-RUN: no files changed. Re-run with --apply to {action} them "
              f"(add --delete to remove instead of archive).")
        return 0

    moved = 0
    for m in manifests:
        if not m.is_file():
            continue
        if args.delete:
            m.unlink()
        else:
            target = _archive_target(repo_root, m)
            target.parent.mkdir(parents=True, exist_ok=True)
            m.replace(target)
        moved += 1
    verb = "deleted" if args.delete else f"archived under {repo_root / 'state' / '_archive' / 'resolved_datasets'}"
    print(f"\n{action.upper()} complete: {moved} manifest(s) {verb}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
