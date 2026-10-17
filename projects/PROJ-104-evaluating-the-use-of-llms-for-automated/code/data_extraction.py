"""Data extraction script for T003.

This script uses the GitHub API (via PyGithub) to fetch commit
information from the five target repositories. It collects commits
from the last two years that modify documentation files
(extensions .md, .rst, .txt) and writes a CSV file
`data/raw/commit_pairs.csv` with the required fields:

    commit_hash,commit_message,repository_name,doc_diff,timestamp

After writing the CSV it computes its SHA‑256 checksum and records it
in `data/metadata.yaml`. A log entry reports how many commits were
skipped because they did not modify documentation files.

The script is intended to be run via:
    python -m code.data_extraction
"""
from __future__ import annotations

import csv
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import yaml
from github import Github

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPOS = {
    "pandas": "pandas-dev/pandas",
    "requests": "psf/requests",
    "scikit-learn": "scikit-learn/scikit-learn",
    "flask": "pallets/flask",
    "django": "django/django",
}

# Two‑year window (relative to now)
SINCE_DATE = (datetime.utcnow() - timedelta(days=2 * 365)).date()

# Minimum number of pairs required by the specification
MIN_PAIRS = 500

# Output locations
CSV_PATH = paths.data("raw", "commit_pairs.csv")
METADATA_PATH = paths.data("metadata.yaml")

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def write_csv(rows: List[dict]) -> None:
    """Write rows to the CSV file with the required header order."""
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "commit_hash",
        "commit_message",
        "repository_name",
        "doc_diff",
        "timestamp",
    ]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log.info("Wrote %d rows to %s", len(rows), CSV_PATH)

def update_metadata(file_path: Path) -> None:
    """Compute SHA‑256 of file_path and store it in data/metadata.yaml."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if METADATA_PATH.exists():
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}
    # Store path relative to project root
    rel_path = str(file_path.relative_to(paths.root))
    data[rel_path] = checksum
    with METADATA_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    log.info("Recorded checksum for %s in %s", file_path.name, METADATA_PATH)

# ----------------------------------------------------------------------
# Main extraction logic using PyGithub
# ----------------------------------------------------------------------
def extract_commit_pairs() -> List[dict]:
    """Iterate over the target repositories and collect commit‑pair rows."""
    rows: List[dict] = []
    skipped = 0
    g = Github()  # unauthenticated; respects rate limits

    for repo_label, repo_full_name in REPOS.items():
        log.info("Processing repository %s (%s)", repo_label, repo_full_name)
        repo = g.get_repo(repo_full_name)

        for commit in repo.get_commits():
            # Stop early if we already have enough rows
            if len(rows) >= MIN_PAIRS:
                log.info("Reached required %d commit‑pair rows; stopping early.", MIN_PAIRS)
                return rows

            commit_date = commit.commit.author.date
            if commit_date.date() < SINCE_DATE:
                # Commits are ordered newest‑first; once we hit older than window we can break.
                break

            # Gather documentation files changed in this commit
            doc_files = [
                f
                for f in commit.files
                if f.filename.lower().endswith((".md", ".rst", ".txt"))
            ]

            if not doc_files:
                skipped += 1
                continue

            # Build a concatenated diff for all documentation files in this commit
            doc_diff = "\n".join(
                (f.patch or "") for f in doc_files
            ).strip()

            if not doc_diff:
                # No diff content (unlikely but possible); treat as no doc change.
                skipped += 1
                continue

            row = {
                "commit_hash": commit.sha,
                "commit_message": commit.commit.message,
                "repository_name": repo.full_name,
                "doc_diff": doc_diff,
                "timestamp": commit.commit.author.date.isoformat(),
            }
            rows.append(row)

        log.info(
            "Finished repo %s: collected %d rows so far, %d commits skipped (no doc change).",
            repo_label,
            len(rows),
            skipped,
        )

    log.info(
        "Extraction finished: %d rows collected, %d commits skipped (no doc change).",
        len(rows),
        skipped,
    )
    return rows

def main() -> int:
    """Run the extraction pipeline and write outputs."""
    rows = extract_commit_pairs()
    if len(rows) < MIN_PAIRS:
        log.error(
            "Insufficient commit‑pair rows collected: %d (required %d).",
            len(rows),
            MIN_PAIRS,
        )
        return 1

    write_csv(rows)
    update_metadata(CSV_PATH)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
