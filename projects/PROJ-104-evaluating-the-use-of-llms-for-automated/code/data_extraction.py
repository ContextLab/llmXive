"""Data extraction script for T003.

This script clones the five target repositories, walks the last two
years of commit history, extracts commits that modify documentation
files (.md or .rst), and writes a CSV file
`data/raw/commit_pairs.csv` with the required fields:

    commit_hash,commit_message,repository_name,doc_diff,timestamp

After writing the CSV it computes its SHA‑256 checksum and records it
in `data/metadata.yaml`.  A log entry reports how many commits were
skipped because they did not modify documentation files.

The script is intended to be run via:
    python -m code.data_extraction
"""
from __future__ import annotations

import csv
import hashlib
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

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
SINCE_DATE = (datetime.utcnow() - timedelta(days=2 * 365)).date().isoformat()

# Minimum number of pairs required by the specification
MIN_PAIRS = 500

# Output locations
CSV_PATH = paths.data("raw", "commit_pairs.csv")
METADATA_PATH = paths.data("metadata.yaml")

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def run_git(args: List[str], cwd: Path | None = None) -> str:
    """Run a git command and return its stdout as a string."""
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()

def clone_repo(name: str, url: str, dest: Path) -> None:
    """Clone a repository shallowly (only commits from the last two years)."""
    if dest.exists():
        log.info("Repo %s already cloned at %s", name, dest)
        return
    log.info("Cloning %s into %s (shallow since %s)", name, dest, SINCE_DATE)
    # --filter=blob:none reduces download size; --shallow-since limits history.
    run_git(
        [
            "clone",
            "--depth=1",
            f"--shallow-since={SINCE_DATE}",
            "--filter=blob:none",
            "--no-checkout",
            url,
            str(dest),
        ]
    )
    # Checkout the working tree (needed for diff generation)
    run_git(["checkout", "HEAD"], cwd=dest)

def get_commits(repo_dir: Path) -> List[str]:
    """Return a list of commit hashes in the last two years (newest first)."""
    log.info("Listing commits for %s since %s", repo_dir.name, SINCE_DATE)
    commits = run_git(
        ["rev-list", "--since", SINCE_DATE, "--all"],
        cwd=repo_dir,
    ).splitlines()
    return commits

def commit_modifies_doc(repo_dir: Path, commit: str) -> List[str]:
    """Return a list of documentation files (.md/.rst) changed in the commit."""
    changed = run_git(
        ["diff-tree", "--no-commit-id", "--name-only", "-r", commit],
        cwd=repo_dir,
    ).splitlines()
    doc_files = [f for f in changed if f.lower().endswith((".md", ".rst"))]
    return doc_files

def get_commit_message(repo_dir: Path, commit: str) -> str:
    return run_git(
        ["log", "-1", "--format=%B", commit],
        cwd=repo_dir,
    )

def get_commit_timestamp(repo_dir: Path, commit: str) -> str:
    """Return ISO‑8601 timestamp of the commit (author date)."""
    return run_git(
        ["show", "-s", "--format=%cI", commit],
        cwd=repo_dir,
    )

def get_doc_diff(repo_dir: Path, commit: str, files: List[str]) -> str:
    """Return the diff for the given documentation files in a commit."""
    # Use git show to get the diff for the selected files only.
    diff_parts = []
    for f in files:
        diff = run_git(
            ["show", commit, "--", f],
            cwd=repo_dir,
        )
        diff_parts.append(diff)
    return "\n".join(diff_parts)

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
    # Preserve any existing entries; we only need to ensure this file is recorded.
    try:
        import yaml

        if METADATA_PATH.exists():
            with METADATA_PATH.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}
    except Exception as e:
        log.error("Failed to read existing metadata.yaml: %s", e)
        data = {}
    data[str(file_path.relative_to(paths.root))] = checksum
    with METADATA_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    log.info("Recorded checksum for %s in %s", file_path.name, METADATA_PATH)

# ----------------------------------------------------------------------
# Main extraction logic
# ----------------------------------------------------------------------
def extract_commit_pairs() -> List[dict]:
    """Iterate over the target repositories and collect commit‑pair rows."""
    rows: List[dict] = []
    skipped = 0

    for repo_name, repo_url in REPOS.items():
        clone_dir = paths.data("raw", "cloned_repos", repo_name)
        clone_repo(repo_name, repo_url, clone_dir)

        commits = get_commits(clone_dir)
        log.info("Found %d commits in %s", len(commits), repo_name)

        for commit_hash in commits:
            doc_files = commit_modifies_doc(clone_dir, commit_hash)
            if not doc_files:
                skipped += 1
                continue

            # Build the row
            row = {
                "commit_hash": commit_hash,
                "commit_message": get_commit_message(clone_dir, commit_hash),
                "repository_name": repo_name,
                "doc_diff": get_doc_diff(clone_dir, commit_hash, doc_files),
                "timestamp": get_commit_timestamp(clone_dir, commit_hash),
            }
            rows.append(row)

            if len(rows) >= MIN_PAIRS:
                log.info(
                    "Reached required %d commit‑pair rows; stopping early.",
                    MIN_PAIRS,
                )
                return rows

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
    sys.exit(main())
