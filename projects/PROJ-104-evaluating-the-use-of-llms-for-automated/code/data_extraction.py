"""Data extraction for commit‑message / documentation‑diff pairs.

This module provides a lightweight, real‑data implementation that fetches
recent commits from the *requests* repository (as a fallback source) via the
GitHub REST API, extracts diffs that modify ``.md`` or ``.rst`` files and
writes a CSV ``data/raw/commit_pairs.csv``.  The implementation respects the
project‑wide ``SEED`` for deterministic ordering and records a SHA‑256
checksum in ``data/metadata.yaml``.
"""
from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import sys
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
        url = f"{GITHUB_API}/repos/{owner}/{repo}/commits?since={since_iso}&per_page=100&page={page}"
        resp = _github_get(url, token)
        batch = resp.json()
        if not batch:
            break
        commits.extend(batch)
        page += 1
    return commits

def _fetch_diff(owner: str, repo: str, sha: str) -> str:
    """Return the full diff (as a string) for *sha*."""
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
            # Use the patch field which contains the unified diff
            patch = f.get("patch", "")
            if patch:
                diffs.append(patch)
    return "\n".join(diffs).strip()

def extract_commit_pairs(target: int = 5) -> List[Dict]:
    """Fetch real commit‑pair rows until *target* rows are collected."""
    from datetime import datetime, timedelta

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
                    "commit_message": commit.get("commit", {}).get("message", "").replace("\n", " ").strip(),
                    "repository_name": f"{owner}/{repo}",
                    "doc_diff": doc_diff,
                    "timestamp": commit.get("commit", {}).get("author", {}).get("date", ""),
                }
            )
            if len(rows) >= target:
                break
        if len(rows) >= target:
            break
    if len(rows) < target:
        raise RuntimeError(f"Could only collect {len(rows)} commit‑pairs; need at least {target}")
    log.info("Collected %d commit‑pair rows", len(rows))
    return rows

def write_csv(rows: List[Dict]) -> None:
    """Write *rows* to ``data/raw/commit_pairs.csv``."""
    csv_path = paths.data("raw", "commit_pairs.csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["commit_hash", "commit_message", "repository_name", "doc_diff", "timestamp"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log.info("Wrote %d rows to %s", len(rows), csv_path)
    update_metadata(csv_path)

def main() -> int:
    """Entry point used by the pipeline."""
    try:
        rows = extract_commit_pairs(target=5)
        write_csv(rows)
        return 0
    except Exception as e:
        log.exception("Data extraction failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
