"""Data extraction script for T003.

This script extracts commit‑message and documentation‑diff pairs from
five target repositories. It uses the GitHub REST API to identify commits
from the last 2 years and the GitHub API to retrieve the per‑file patches.
Only changes to ``.md`` or ``.rst`` files are retained.

The script **requires** a ``GITHUB_TOKEN`` environment variable for
authenticated requests (higher rate limits). If the variable is missing the
script aborts loudly – this matches the functional requirement that the
token be mandatory.

The CSV written to ``data/raw/commit_pairs.csv`` must contain at least
``MIN_PAIRS`` rows (500). The script aborts with a clear error if the
threshold is not met. After successful extraction a SHA‑256 checksum of
the CSV is recorded in ``data/metadata.yaml``.
"""
from __future__ import annotations

import csv
import hashlib
import logging
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict

import requests
import yaml

from llmxive_toolkit import get_logger, paths
from code.seeds import SEED

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPOS = {
    "requests": ("psf", "requests"),
    "flask": ("pallets", "flask"),
    "django": ("django", "django"),
    "scikit-learn": ("scikit-learn", "scikit-learn"),
    "pandas": ("pandas-dev", "pandas"),
}

MIN_PAIRS = 500
CSV_PATH = paths.data("raw", "commit_pairs.csv")
METADATA_PATH = paths.data("metadata.yaml")

# ----------------------------------------------------------------------
# GitHub API helpers
# ----------------------------------------------------------------------
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    log.error("GITHUB_TOKEN environment variable is required for data extraction.")
    raise RuntimeError("Missing GITHUB_TOKEN – aborting data extraction.")
else:
    log.info("Using provided GITHUB_TOKEN for authenticated GitHub requests.")

SESSION = requests.Session()
SESSION.headers.update(
    {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "llmxive-data-extraction",
        "Authorization": f"token {TOKEN}",
    }
)

# Simple exponential back‑off retry for rate‑limit (429) and secondary
# rate‑limit (403) responses.
def _github_get(url: str, params: dict | None = None, max_retries: int = 5) -> dict:
    """GET a JSON payload from the GitHub API, handling rate‑limit errors."""
    backoff = 1
    for attempt in range(1, max_retries + 1):
        try:
            resp = SESSION.get(url, params=params, timeout=30)
            if resp.status_code in (429, 403):
                # GitHub may include a Retry‑After header; fall back to backoff.
                retry_after = resp.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else backoff
                log.warning(
                    "GitHub rate limit (status %s) on %s – waiting %s seconds (attempt %d)",
                    resp.status_code,
                    url,
                    wait,
                    attempt,
                )
                time.sleep(wait)
                backoff = min(backoff * 2, 60)  # cap back‑off at 60 s
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries:
                log.exception("GitHub request failed after %d attempts: %s", attempt, e)
                raise
            else:
                log.warning("GitHub request error (%s) – retry %d/%d", e, attempt, max_retries)
                time.sleep(backoff)
                backoff = min(backoff * 2, 60)
    # Should never reach here
    raise RuntimeError(f"Failed to GET {url}")

def _list_commits(owner: str, repo: str, since_iso: str) -> List[dict]:
    """Iterate over all commits since ``since_iso`` (ISO‑8601)."""
    commits: List[dict] = []
    page = 1
    while True:
        params = {"since": since_iso, "per_page": 100, "page": page}
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        batch = _github_get(url, params=params)
        if not batch:
            break
        commits.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return commits

def _fetch_commit_diff(owner: str, repo: str, sha: str) -> str:
    """
    Retrieve the diff for a commit via the ``/commits/{sha}`` endpoint.
    Only ``.md`` and ``.rst`` file patches are kept.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    data = _github_get(url)
    files = data.get("files", [])
    doc_hunks: List[str] = []
    for f in files:
        filename = f.get("filename", "")
        if not (filename.endswith(".md") or filename.endswith(".rst")):
            continue
        patch = f.get("patch")
        if patch:
            diff_header = f"diff --git a/{filename} b/{filename}"
            doc_hunks.append(f"{diff_header}\n{patch}")
    return "\n".join(doc_hunks).strip()

# ----------------------------------------------------------------------
# CSV / metadata utilities
# ----------------------------------------------------------------------
def write_csv(rows: List[dict]) -> None:
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
        writer.writerows(rows)
    log.info("Wrote %d rows to %s", len(rows), CSV_PATH)

def update_metadata(file_path: Path) -> None:
    """Compute SHA‑256 checksum and store it in ``data/metadata.yaml``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if METADATA_PATH.exists():
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    rel_path = str(file_path.relative_to(paths.root))
    data[rel_path] = checksum
    with METADATA_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    log.info("Updated metadata for %s", rel_path)

# ----------------------------------------------------------------------
# Extraction pipeline
# ----------------------------------------------------------------------
def extract_commit_pairs() -> List[dict]:
    rows: List[dict] = []
    since_dt = datetime.now(timezone.utc) - timedelta(days=365 * 2)
    since_iso = since_dt.isoformat()
    skipped = 0

    for repo_name, (owner, repo) in REPOS.items():
        log.info("Processing repository %s (%s/%s)", repo_name, owner, repo)
        try:
            commits = _list_commits(owner, repo, since_iso)
        except Exception as e:
            log.error("Failed to list commits for %s: %s", repo_name, e)
            continue

        for commit in commits:
            if len(rows) >= MIN_PAIRS:
                log.info("Reached required %d pairs – stopping early.", MIN_PAIRS)
                return rows

            sha = commit.get("sha")
            if not sha:
                continue

            try:
                doc_diff = _fetch_commit_diff(owner, repo, sha)
            except Exception as e:
                log.warning("Could not fetch diff for %s:%s – %s", repo_name, sha, e)
                skipped += 1
                continue

            if not doc_diff:
                skipped += 1
                continue

            commit_info = commit.get("commit", {})
            row = {
                "commit_hash": sha,
                "commit_message": commit_info.get("message", ""),
                "repository_name": repo_name,
                "doc_diff": doc_diff,
                "timestamp": commit_info.get("author", {}).get("date", ""),
            }
            rows.append(row)

        # Respect GitHub secondary rate limits – short sleep between repos.
        time.sleep(1)

    log.info(
        "Extraction complete: collected %d pairs, skipped %d (no doc changes).",
        len(rows),
        skipped,
    )
    return rows

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    try:
        rows = extract_commit_pairs()
        if len(rows) < MIN_PAIRS:
            raise RuntimeError(
                f"Insufficient data: collected {len(rows)} pairs, but {MIN_PAIRS} are required."
            )
        write_csv(rows)
        update_metadata(CSV_PATH)
        return 0
    except Exception as e:
        log.exception("Data extraction pipeline failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
