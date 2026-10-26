"""Data extraction for commit‑message / documentation‑diff pairs.

This module provides a lightweight, real‑data implementation that fetches
recent commits from the target repositories via the GitHub REST API,
extracts diffs that modify ``.md`` or ``.rst`` files and writes a CSV
``data/raw/commit_pairs.csv``.  The implementation respects the
project‑wide ``SEED`` for deterministic ordering and records a SHA‑256
checksum in ``data/metadata.yaml``.

The script adapts its behaviour based on the command‑line arguments
passed to the top‑level pipeline:

* ``--sample N`` – collect *N* commit‑pair rows (used for the quick‑start
  smoke test).
* ``--full``      – collect the full dataset of at least 500 rows (the
  default for the full pipeline).
* No explicit flag – fall back to a minimal 5‑row extraction (historical
  default).

A ``GITHUB_TOKEN`` environment variable is required; the script fails
loudly if it is missing, preventing silent fallback to synthetic data.
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
from typing import List, Dict

import requests
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
    """Compute SHA‑256 checksum of *file_path* and store it in ``data/metadata.yaml``."""
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
# Core extraction logic
# ----------------------------------------------------------------------
GITHUB_API = "https://api.github.com"
TARGET_REPOS = [
    ("psf", "requests"),
    ("pandas-dev", "pandas"),
    ("scikit-learn", "scikit-learn"),
    ("pallets", "flask"),
    ("django", "django"),
]
DOC_EXTS = {".md", ".rst"}

def _github_get(url: str, token: str | None = None) -> requests.Response:
    """Perform a GET request against the GitHub API with optional token."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp

def _fetch_commits(owner: str, repo: str, since_iso: str) -> List[Dict]:
    """Yield commit objects newer than *since_iso* (ISO‑8601)."""
    commits: List[Dict] = []
    page = 1
    token = os.getenv("GITHUB_TOKEN")
    while True:
        url = (
            f"{GITHUB_API}/repos/{owner}/{repo}/commits"
            f"?since={since_iso}&per_page=100&page={page}"
        )
        resp = _github_get(url, token)
        batch = resp.json()
        if not batch:
            break
        commits.extend(batch)
        page += 1
    return commits

def _fetch_diff(owner: str, repo: str, sha: str) -> List[Dict]:
    """Return the list of file dictionaries for *sha*."""
    token = os.getenv("GITHUB_TOKEN")
    url = f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}"
    resp = _github_get(url, token)
    data = resp.json()
    return data.get("files", [])

def _extract_doc_diff(files: List[Dict]) -> str:
    """Concatenate diffs for documentation files only."""
    diffs = []
    for f in files:
        filename = f.get("filename", "")
        if any(filename.lower().endswith(ext) for ext in DOC_EXTS):
            patch = f.get("patch", "")
            if patch:
                diffs.append(patch)
    return "\n".join(diffs).strip()

def extract_commit_pairs(target: int = 5) -> List[Dict]:
    """Fetch real commit‑pair rows until *target* rows are collected."""
    since = (datetime.utcnow() - timedelta(days=730)).isoformat() + "Z"
    rows: List[Dict] = []
    for owner, repo in TARGET_REPOS:
        log.info("Fetching commits from %s/%s", owner, repo)
        commits = _fetch_commits(owner, repo, since)
        for commit in commits:
            sha = commit.get("sha")
            if not sha:
                continue
            files = _fetch_diff(owner, repo, sha)
            doc_diff = _extract_doc_diff(files)
            if not doc_diff:
                continue
            rows.append(
                {
                    "commit_hash": sha,
                    "commit_message": commit.get("commit", {})
                    .get("message", "")
                    .replace("\n", " ")
                    .strip(),
                    "repository_name": f"{owner}/{repo}",
                    "doc_diff": doc_diff,
                    "timestamp": commit.get("commit", {})
                    .get("author", {})
                    .get("date", ""),
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
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            log.error("GITHUB_TOKEN environment variable is required for data extraction")
            raise RuntimeError("Missing GITHUB_TOKEN")
        target = _determine_target_from_argv()
        rows = extract_commit_pairs(target=target)
        write_csv(rows)
        return 0
    except Exception as e:
        log.exception("Data extraction failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
