"""Data extraction script for T003.

This script clones the five target repositories locally and walks the last
two years of commit history to find commits that modify documentation files
(extensions .md, .rst, .txt). For each qualifying commit it records
`commit_hash`, `commit_message`, `repository_name`, `doc_diff`, and
`timestamp` according to `commitpair.schema.yaml`. After writing the CSV
it computes its SHA‑256 checksum and records it in `data/metadata.yaml`.

The script is intended to be run via:
    python -m code.data_extraction
or indirectly via `code.run_pipeline --full`.
"""
from __future__ import annotations

import csv
import hashlib
import logging
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import yaml

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPOS = {
    "pandas": "https://github.com/pandas-dev/pandas.git",
    "requests": "https://github.com/psf/requests.git",
    "scikit-learn": "https://github.com/scikit-learn/scikit-learn.git",
    "flask": "https://github.com/pallets/flask.git",
    "django": "https://github.com/django/django.git",
}

# Two‑year window (relative to now)
SINCE_DATE = (datetime.now(timezone.utc) - timedelta(days=2 * 365)).date()

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
    """Clone a repo if not already cloned."""
    if dest.exists():
        log.info("Repo already cloned at %s, pulling latest.", dest)
        _run_git(["pull"], cwd=dest)
    else:
        log.info("Cloning %s into %s", repo_url, dest)
        _run_git(["clone", "--depth", "1", repo_url, str(dest)], cwd=dest.parent)

def _fetch_full_history(repo_path: Path) -> None:
    """Ensure we have enough history (at least two years)."""
    # Unshallow the repository to get full history if it was shallow.
    try:
        _run_git(["fetch", "--unshallow"], cwd=repo_path)
    except subprocess.CalledProcessError:
        # Repository may already be complete; ignore errors.
        pass

def _iter_commits(repo_path: Path) -> List[dict]:
    """Yield commit dictionaries for commits within the two‑year window."""
    # git log with %H (hash) %ct (unix timestamp) %s (subject)
    log_output = _run_git(
        [
            "log",
            "--since=2.years",
            "--pretty=format:%H|%ct|%s",
        ],
        cwd=repo_path,
    )
    commits = []
    for line in log_output.splitlines():
        if not line.strip():
            continue
        commit_hash, ts_str, subject = line.split("|", 2)
        commit_dt = datetime.fromtimestamp(int(ts_str), tz=timezone.utc)
        if commit_dt.date() < SINCE_DATE:
            continue
        commits.append(
            {
                "hash": commit_hash,
                "timestamp": commit_dt.isoformat(),
                "message": subject,
            }
        )
    return commits

def _doc_files_changed(repo_path: Path, commit_hash: str) -> List[str]:
    """Return list of documentation file paths changed in the commit."""
    diff_output = _run_git(
        ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash],
        cwd=repo_path,
    )
    files = [
        f
        for f in diff_output.splitlines()
        if f.lower().endswith((".md", ".rst", ".txt"))
    ]
    return files

def _get_doc_diff(repo_path: Path, commit_hash: str, files: List[str]) -> str:
    """Return concatenated diff for the given files in the commit."""
    if not files:
        return ""
    # Use git show to get patches for the selected files
    diff_parts = []
    for f in files:
        try:
            patch = _run_git(
                ["show", f"{commit_hash}:{f}"], cwd=repo_path
            )
        except subprocess.CalledProcessError:
            # fallback to diff view if the file was deleted/added
            patch = _run_git(
                ["show", commit_hash, "--", f], cwd=repo_path
            )
        diff_parts.append(patch)
    return "\n".join(diff_parts).strip()

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
        _fetch_full_history(repo_path)

        log.info("Processing repository %s (%s)", repo_label, repo_url)

        for commit in _iter_commits(repo_path):
            if len(rows) >= MIN_PAIRS:
                log.info(
                    "Reached required %d commit‑pair rows; stopping early.", MIN_PAIRS
                )
                return rows

            doc_files = _doc_files_changed(repo_path, commit["hash"])
            if not doc_files:
                skipped += 1
                continue

            doc_diff = _get_doc_diff(repo_path, commit["hash"], doc_files)
            if not doc_diff:
                skipped += 1
                continue

            row = {
                "commit_hash": commit["hash"],
                "commit_message": commit["message"],
                "repository_name": repo_label,
                "doc_diff": doc_diff,
                "timestamp": commit["timestamp"],
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
