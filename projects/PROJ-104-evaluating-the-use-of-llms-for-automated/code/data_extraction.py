"""Data extraction script for T003.

This script uses the GitHub REST API to retrieve commit‑message /
documentation‑diff pairs from the five target repositories. It
respects the specification's requirement of ≥ 500 pairs, writes the
CSV to ``data/raw/commit_pairs.csv`` and records a SHA‑256 checksum
in ``data/metadata.yaml``.

The implementation avoids cloning full repositories, which speeds up
execution and prevents time‑outs on the CI runner. A personal access
token must be supplied via the ``GITHUB_TOKEN`` environment variable;
the script fails loudly if the token is missing.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

import requests
import yaml

from llmxive_toolkit import get_logger, paths

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Repositories are processed in order of expected size (smaller first)
REPOS = {
    "requests": ("psf", "requests"),
    "flask": ("pallets", "flask"),
    "django": ("django", "django"),
    "scikit-learn": ("scikit-learn", "scikit-learn"),
    "pandas": ("pandas-dev", "pandas"),
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
    rel_path = str(file_path.relative_to(paths.root))
    data[rel_path] = checksum
    with METADATA_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    log.info("Recorded checksum for %s in %s", file_path.name, METADATA_PATH)

# ----------------------------------------------------------------------
# GitHub API helpers
# ----------------------------------------------------------------------
GITHUB_API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "Environment variable GITHUB_TOKEN is required for data extraction."
    )

SESSION = requests.Session()
SESSION.headers.update(
    {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmxive-data-extraction",
    }
)

def _github_get(url: str, params: dict | None = None) -> dict:
    """GET a GitHub API endpoint, raise on error."""
    resp = SESSION.get(url, params=params, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(
            f"GitHub API request failed [{resp.status_code}]: {url}\n{resp.text}"
        )
    return resp.json()

def _list_commits(owner: str, repo: str, since_iso: str) -> List[dict]:
    """Return a list of commit metadata dictionaries (paginated)."""
    commits: List[dict] = []
    page = 1
    per_page = 100
    while True:
        params = {
            "since": since_iso,
            "per_page": per_page,
            "page": page,
        }
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits"
        batch = _github_get(url, params=params)
        if not batch:
            break
        commits.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return commits

def _get_commit_detail(owner: str, repo: str, sha: str) -> dict:
    """Fetch detailed commit information, including file list and patches."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    return _github_get(url)

def _extract_doc_diff(files: List[dict]) -> str:
    """Concatenate patches for .md and .rst files."""
    diffs = []
    for f in files:
        filename = f.get("filename", "")
        if filename.lower().endswith((".md", ".rst")) and f.get("patch"):
            diffs.append(f["patch"])
    return "\n".join(diffs).strip()

# ----------------------------------------------------------------------
# Main extraction logic
# ----------------------------------------------------------------------
def extract_commit_pairs() -> List[dict]:
    """Iterate over the target repositories and collect commit‑pair rows."""
    rows: List[dict] = []
    # Use a date two years ago from now in ISO‑8601 format
    since_dt = datetime.now(timezone.utc) - timedelta(days=365 * 2)
    since_iso = since_dt.isoformat()

    for repo_name, (owner, repo) in REPOS.items():
        log.info("Fetching commits for %s/%s", owner, repo)
        commits = _list_commits(owner, repo, since_iso)
        log.info("Found %d commits (including non‑doc) for %s", len(commits), repo_name)

        for commit in commits:
            if len(rows) >= MIN_PAIRS:
                log.info(
                    "Reached required %d commit‑pair rows; stopping early.", MIN_PAIRS
                )
                return rows

            sha = commit.get("sha")
            if not sha:
                continue

            detail = _get_commit_detail(owner, repo, sha)
            files = detail.get("files", [])
            doc_diff = _extract_doc_diff(files)
            if not doc_diff:
                continue  # no documentation change

            commit_message = detail.get("commit", {}).get("message", "")
            timestamp = detail.get("commit", {}).get("author", {}).get("date", "")
            if not timestamp:
                continue

            row = {
                "commit_hash": sha,
                "commit_message": commit_message,
                "repository_name": repo_name,
                "doc_diff": doc_diff,
                "timestamp": timestamp,
            }
            rows.append(row)

        log.info(
            "Repo %s: collected %d rows so far.", repo_name, len(rows)
        )

    log.info(
        "Extraction finished: %d rows collected.", len(rows)
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
