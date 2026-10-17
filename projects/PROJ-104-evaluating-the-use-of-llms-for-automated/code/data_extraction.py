"""Data extraction script for T003.

This script clones the five target repositories locally and walks the last
two years of commit history to find commits that modify documentation files
(extensions .md, .rst). For each qualifying commit it records
`commit_hash`, `commit_message`, `repository_name`, `doc_diff`, and
`timestamp` according to `commitpair.schema.yaml`. After writing the CSV
it computes its SHA‑256 checksum and records it in `data/metadata.yaml`.

The script is optimized to avoid timeouts by using git-native filtering
to only iterate over commits that touch documentation files.
"""
from __future__ import annotations

import csv
import hashlib
import logging
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List

import yaml

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Reordered to process smaller/faster repos first to reach MIN_PAIRS quickly
REPOS = {
    "requests": "https://github.com/psf/requests.git",
    "flask": "https://github.com/pallets/flask.git",
    "django": "https://github.com/django/django.git",
    "scikit-learn": "https://github.com/scikit-learn/scikit-learn.git",
    "pandas": "https://github.com/pandas-dev/pandas.git",
}

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
# Git helpers
# ----------------------------------------------------------------------
def _run_git(args: List[str], cwd: Path) -> str:
    """Run a git command and return stdout as string."""
    result = subprocess.run(
        ["git"] + args,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return result.stdout

def _clone_repo(repo_url: str, dest: Path) -> None:
    """Clone a repo if not already cloned. Use shallow-since to optimize."""
    if dest.exists():
        log.info("Repo already cloned at %s, pulling latest.", dest)
        try:
            _run_git(["pull"], cwd=dest)
        except subprocess.CalledProcessError:
            log.warning("Pull failed for %s; may need to re-clone.", dest)
    else:
        log.info("Cloning %s into %s (shallow since 2 years)", repo_url, dest)
        # Shallow since 2 years is the most efficient way to get the required window
        _run_git(["clone", "--shallow-since=2.years", repo_url, str(dest)], cwd=dest.parent)

def _get_combined_doc_diff(repo_path: Path, commit_hash: str) -> str:
    """Return concatenated diff for documentation files in the commit."""
    try:
        # Filter the show command to only include .md and .rst files
        return _run_git(["show", commit_hash, "--", "*.md", "*.rst"], cwd=repo_path).strip()
    except subprocess.CalledProcessError:
        return ""

# ----------------------------------------------------------------------
# Main extraction logic
# ----------------------------------------------------------------------
def extract_commit_pairs() -> List[dict]:
    """Iterate over the target repositories and collect commit‑pair rows."""
    rows: List[dict] = []
    skipped = 0

    repos_base = paths.data("repos")
    repos_base.mkdir(parents=True, exist_ok=True)

    for repo_label, repo_url in REPOS.items():
        repo_path = repos_base / repo_label
        _clone_repo(repo_url, repo_path)

        log.info("Processing repository %s (%s)", repo_label, repo_url)

        # OPTIMIZATION: Use git log to filter ONLY commits that touch .md or .rst files
        # Format: hash <null> unix_timestamp <null> full_body
        log_output = _run_git(
            [
                "log",
                "--since=2.years",
                "--pretty=format:%H%x00%ct%x00%B",
                "--",
                "*.md",
                "*.rst",
            ],
            cwd=repo_path,
        )

        for line in log_output.splitlines():
            if not line.strip():
                continue
            
            # Split by null byte to safely separate hash, timestamp, and message
            parts = line.split("\x00")
            if len(parts) < 3:
                continue
            
            commit_hash, ts_str, message = parts[0], parts[1], parts[2]
            
            if len(rows) >= MIN_PAIRS:
                log.info("Reached required %d commit‑pair rows; stopping early.", MIN_PAIRS)
                return rows

            doc_diff = _get_combined_doc_diff(repo_path, commit_hash)
            if not doc_diff:
                skipped += 1
                continue

            # Convert unix timestamp to ISO-8601
            commit_dt = datetime.fromtimestamp(int(ts_str), tz=timezone.utc)
            
            row = {
                "commit_hash": commit_hash,
                "commit_message": message,
                "repository_name": repo_label,
                "doc_diff": doc_diff,
                "timestamp": commit_dt.isoformat(),
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
    try:
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
    except Exception as e:
        log.exception("Data extraction failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())