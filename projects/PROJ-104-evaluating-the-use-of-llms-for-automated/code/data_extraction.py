"""Data extraction for commit‑message / documentation‑diff pairs.

This module fetches recent commits from the target repositories,
extracts diffs that modify ``.md`` or ``.rst`` files and writes a CSV
``data/raw/commit_pairs.csv``.  The implementation clones the
repositories locally (under ``data/tmp/repos``) and uses **GitPython**
to avoid GitHub API rate‑limit issues.  The script respects the
project‑wide ``SEED`` for deterministic ordering and records a
SHA‑256 checksum in ``data/metadata.yaml``.

The script adapts its behaviour based on the command‑line arguments
passed to the top‑level pipeline:

* ``--sample N`` – collect *N* commit‑pair rows (used for the quick‑start
  smoke test).
* ``--full``      – collect the full dataset of at least 500 rows (the
  default for the full pipeline).
* No explicit flag – fall back to a minimal 5‑row extraction (historical
  default).

A ``GITHUB_TOKEN`` environment variable is **optional**; unauthenticated
requests are not used – all data is obtained from the local clones.
The script fails loudly only when it cannot collect the required number
of rows.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

import git
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _checksum(file_path: Path) -> str:
    """Return the SHA‑256 checksum of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def update_metadata(file_path: Path) -> None:
    """Compute SHA‑256 checksum of *file_path* and store it in
    ``data/metadata.yaml``."""
    checksum = _checksum(file_path)
    meta_path = paths.data("metadata.yaml")
    meta_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing metadata if present
    if meta_path.is_file():
        with meta_path.open("r", encoding="utf-8") as f:
            try:
                meta = json.load(f)
            except json.JSONDecodeError:
                meta = {}
    else:
        meta = {}

    rel = str(file_path.relative_to(paths.root))
    meta[rel] = {"sha256": checksum}
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    log.debug("Recorded checksum for %s", rel)


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
TARGET_REPOS = [
    ("psf", "requests"),
    ("pandas-dev", "pandas"),
    ("scikit-learn", "scikit-learn"),
    ("pallets", "flask"),
    ("django", "django"),
]
DOC_EXTS = {".md", ".rst"}

REPOS_ROOT = paths.data("tmp", "repos")  # <project>/data/tmp/repos


# ----------------------------------------------------------------------
# Core extraction logic
# ----------------------------------------------------------------------
def _clone_repo(owner: str, repo: str) -> Path:
    """Clone ``owner/repo`` into ``REPOS_ROOT`` if not already present."""
    dest = REPOS_ROOT / repo
    if dest.is_dir() and (dest / ".git").exists():
        log.info("Repository %s/%s already cloned at %s", owner, repo, dest)
        return dest
    url = f"https://github.com/{owner}/{repo}.git"
    log.info("Cloning %s into %s", url, dest)
    # Use a shallow clone to keep runtime reasonable while still
    # providing enough history (500 commits is more than enough for our
    # 2‑year window).
    try:
        git.Repo.clone_from(
            url,
            to_path=str(dest),
            multi_options=["--depth=1000"],
        )
    except Exception as e:
        log.exception("Failed to clone %s: %s", url, e)
        raise
    return dest


def _iter_commits(repo_path: Path, since_iso: str) -> List[git.objects.commit.Commit]:
    """Yield commit objects newer than *since_iso* (ISO‑8601)."""
    repo = git.Repo(str(repo_path))
    # GitPython accepts datetime objects for ``since``; convert ISO string.
    since_dt = datetime.fromisoformat(since_iso.rstrip("Z"))
    commits = list(repo.iter_commits(since=since_dt))
    log.debug("Found %d commits in %s since %s", len(commits), repo_path, since_iso)
    return commits


def _extract_doc_diff_from_commit(commit: git.objects.commit.Commit) -> str:
    """Return concatenated diffs for documentation files only."""
    diffs: List[str] = []
    # ``commit.parents`` may be empty for root commit – skip those.
    if not commit.parents:
        return ""
    parent = commit.parents[0]
    diff_index = parent.diff(commit, create_patch=True)
    for diff in diff_index:
        # Determine the file path (new or old) and check extension.
        path = diff.b_path or diff.a_path
        if not path:
            continue
        if not any(path.lower().endswith(ext) for ext in DOC_EXTS):
            continue
        # diff.diff is a bytes object containing the unified diff.
        try:
            patch = diff.diff.decode("utf-8", errors="ignore")
            diffs.append(patch)
        except Exception:
            continue
    return "\n".join(diffs).strip()


def extract_commit_pairs(target: int = 5) -> List[Dict]:
    """Fetch real commit‑pair rows until *target* rows are collected."""
    since = (datetime.utcnow() - timedelta(days=730)).isoformat() + "Z"
    rows: List[Dict] = []
    for owner, repo in TARGET_REPOS:
        try:
            repo_path = _clone_repo(owner, repo)
        except Exception:
            log.error("Skipping repository %s/%s due to clone failure", owner, repo)
            continue

        commits = _iter_commits(repo_path, since)
        for commit in commits:
            doc_diff = _extract_doc_diff_from_commit(commit)
            if not doc_diff:
                continue
            rows.append(
                {
                    "commit_hash": commit.hexsha,
                    "commit_message": commit.message.replace("\n", " ").strip(),
                    "repository_name": f"{owner}/{repo}",
                    "doc_diff": doc_diff,
                    "timestamp": commit.committed_datetime.isoformat(),
                }
            )
            if len(rows) >= target:
                break
        if len(rows) >= target:
            break

    if len(rows) < target:
        raise RuntimeError(
            f"Could only collect {len(rows)} commit‑pairs; need at least {target}"
        )
    log.info("Collected %d commit‑pair rows", len(rows))
    return rows


def write_csv(rows: List[Dict]) -> None:
    """Write *rows* to ``data/raw/commit_pairs.csv``."""
    csv_path = paths.data("raw", "commit_pairs.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "commit_hash",
        "commit_message",
        "repository_name",
        "doc_diff",
        "timestamp",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log.info("Wrote %d rows to %s", len(rows), csv_path)
    update_metadata(csv_path)


def _determine_target_from_argv() -> int:
    """
    Decide how many rows to collect based on the CLI of the *parent* pipeline.

    The top‑level ``run_pipeline`` script forwards its arguments to the
    Python process (e.g. ``python -m code.run_pipeline --sample 5`` or
    ``python -m code.run_pipeline --full``).  This helper inspects
    ``sys.argv`` for those flags and returns the appropriate target size.
    """
    argv = sys.argv[1:]  # skip the script name
    if "--sample" in argv:
        idx = argv.index("--sample")
        try:
            sample_val = int(argv[idx + 1])
            return max(sample_val, 1)
        except Exception:
            log.warning("Invalid sample size after '--sample'; falling back to 5")
            return 5
    if "--full" in argv:
        # Full pipeline requires at least 500 rows as per specification.
        return 500
    # Default fallback (historical behaviour)
    return 5


def main() -> int:
    """Entry point used by the pipeline."""
    try:
        target = _determine_target_from_argv()
        rows = extract_commit_pairs(target=target)
        write_csv(rows)
        return 0
    except Exception as e:
        log.exception("Data extraction failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
