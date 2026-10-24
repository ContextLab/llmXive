"""Data extraction script for T003.

This script extracts commit-message and documentation-diff pairs from
five target repositories. It uses the GitHub REST API to identify commits
from the last 2 years and local git clones to extract the documentation-only
portion of the diffs.

It requires a GITHUB_TOKEN environment variable and ensures at least 500
valid pairs are collected.
"""
from __future__ import annotations

import csv
import hashlib
import logging
import os
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

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
REPOS_ROOT = paths.data("tmp", "repos")

# ----------------------------------------------------------------------
# GitHub API & Git Helpers
# ----------------------------------------------------------------------
TOKEN = os.getenv("GITHUB_TOKEN")
if not TOKEN:
    # Fail loudly as required by specification
    raise RuntimeError("GITHUB_TOKEN environment variable is missing. It is required for data extraction.")

SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "llmxive-data-extraction",
    "Authorization": f"token {TOKEN}",
})

def _github_get(url: str, params: dict | None = None) -> dict:
    resp = SESSION.get(url, params=params, timeout=30)
    if resp.status_code == 403:
        raise RuntimeError(f"GitHub API Rate Limit or Forbidden: {resp.text}")
    resp.raise_for_status()
    return resp.json()

def _clone_repo(repo_name: str, owner: str, repo: str) -> Path:
    dest = REPOS_ROOT / repo_name
    if dest.exists():
        log.info("Repo %s already cloned at %s", repo_name, dest)
        return dest
    
    log.info("Cloning %s/%s into %s...", owner, repo, dest)
    # Use blobless clone to save space and time while preserving history
    try:
        subprocess.run(
            ["git", "clone", "--filter=blob:none", f"https://github.com/{owner}/{repo}.git", str(dest)],
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        log.error("Failed to clone %s: %s", repo_name, e.stderr)
        raise
    return dest

def _get_doc_diff_local(repo_path: Path, sha: str) -> str:
    """Extract only .md and .rst changes from a commit using git show."""
    result = subprocess.run(
        ["git", "-C", str(repo_path), "show", sha],
        capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    if result.returncode != 0:
        return ""
    
    content = result.stdout
    # Split by the git diff marker
    sections = content.split("diff --git")
    doc_hunks = []
    # First element is the commit header, skip it
    for section in sections[1:]:
        # section starts with " a/path b/path ..."
        lines = section.split("\n")
        if not lines:
            continue
        header = lines[0]
        if ".md" in header or ".rst" in header:
            doc_hunks.append("diff --git" + section)
    
    return "\n".join(doc_hunks).strip()

def _list_commits(owner: str, repo: str, since_iso: str) -> List[dict]:
    commits = []
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

# ----------------------------------------------------------------------
# Pipeline Logic
# ----------------------------------------------------------------------
def write_csv(rows: List[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["commit_hash", "commit_message", "repository_name", "doc_diff", "timestamp"]
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    log.info("Wrote %d rows to %s", len(rows), CSV_PATH)

def update_metadata(file_path: Path) -> None:
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if METADATA_PATH.exists():
        with METADATA_PATH.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    
    rel_path = str(file_path.relative_to(paths.root))
    data[rel_path] = checksum
    with METADATA_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)

def extract_commit_pairs() -> List[dict]:
    rows = []
    since_dt = datetime.now(timezone.utc) - timedelta(days=365 * 2)
    since_iso = since_dt.isoformat()
    
    skipped_count = 0

    for repo_name, (owner, repo) in REPOS.items():
        log.info("Processing %s...", repo_name)
        try:
            repo_path = _clone_repo(repo_name, owner, repo)
            commits = _list_commits(owner, repo, since_iso)
        except Exception as e:
            log.error("Failed to initialize %s: %s", repo_name, e)
            continue

        for commit in commits:
            if len(rows) >= MIN_PAIRS:
                return rows

            sha = commit.get("sha")
            if not sha:
                continue

            doc_diff = _get_doc_diff_local(repo_path, sha)
            if not doc_diff:
                skipped_count += 1
                continue

            detail = commit.get("commit", {})
            row = {
                "commit_hash": sha,
                "commit_message": detail.get("message", ""),
                "repository_name": repo_name,
                "doc_diff": doc_diff,
                "timestamp": detail.get("author", {}).get("date", ""),
            }
            rows.append(row)
    
    log.info("Extraction complete. Total pairs: %d. Skipped (no doc change): %d", len(rows), skipped_count)
    return rows

def main() -> int:
    try:
        rows = extract_commit_pairs()
        if len(rows) < MIN_PAIRS:
            # Abort loudly as required by specification
            raise RuntimeError(f"Insufficient data: Collected {len(rows)} pairs, but {MIN_PAIRS} are required.")
        
        write_csv(rows)
        update_metadata(CSV_PATH)
        return 0
    except Exception as e:
        log.exception("Data extraction pipeline failed: %s", e)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())