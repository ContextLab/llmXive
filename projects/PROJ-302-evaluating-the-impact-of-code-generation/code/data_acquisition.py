"""
Data acquisition script for T002.

Streams pull‑request metadata for three high‑profile GitHub repositories
(tensorflow/tensorflow, pytorch/pytorch, numpy/numpy) using the GitHub
REST API.  The script respects API rate limits by applying exponential
back‑off via `tenacity`.  Results are stored as Parquet files under
`data/raw/` and a consolidated commit‑message table is written to
`data/raw/commit_messages.parquet`.

The script can be executed directly:
    python code/data_acquisition.py --stream
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Project‑wide utilities
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
REPOS = [
    ("tensorflow", "tensorflow"),
    ("pytorch", "pytorch"),
    ("numpy", "numpy"),
]

GITHUB_API = "https://api.github.com"
PER_PAGE = 100  # maximum allowed by GitHub
MAX_PAGES = 100  # safety cap

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _auth_headers() -> Dict[str, str]:
    """Return authentication headers if a GITHUB_TOKEN is present."""
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return {"Authorization": f"token {token}"}
    return {}

@retry(
    retry=retry_if_exception_type(requests.exceptions.RequestException),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _get(url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    """GET a URL with exponential back‑off on failures."""
    headers = _auth_headers()
    response = requests.get(url, headers=headers, params=params, timeout=30)
    # Raise for HTTP errors (including 403 rate‑limit)
    if response.status_code == 403:
        # GitHub includes remaining rate‑limit info in headers; we let tenacity retry.
        log.warning("Rate limit hit, backing off: %s", response.text)
    response.raise_for_status()
    return response

def _fetch_all_prs(owner: str, repo: str) -> List[Dict[str, Any]]:
    """Stream all closed PRs for a repository."""
    prs: List[Dict[str, Any]] = []
    for page in range(1, MAX_PAGES + 1):
        params = {
            "state": "closed",
            "per_page": PER_PAGE,
            "page": page,
        }
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls"
        resp = _get(url, params=params)
        batch = resp.json()
        if not batch:
            break
        prs.extend(batch)
        log.info("Fetched %d PRs from %s/%s (page %d)", len(batch), owner, repo, page)
    log.info("Total PRs fetched for %s/%s: %d", owner, repo, len(prs))
    return prs

def _fetch_pr_files(owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Return list of files changed in a PR."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files"
    resp = _get(url)
    return resp.json()

def _fetch_pr_commits(owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
    """Return list of commits for a PR."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/commits"
    resp = _get(url)
    return resp.json()

# ----------------------------------------------------------------------
# Core extraction logic
# ----------------------------------------------------------------------
def extract_repository_data(owner: str, repo: str) -> pd.DataFrame:
    """Extract PR‑level metadata for a given repository."""
    pr_records: List[Dict[str, Any]] = []
    commit_records: List[Dict[str, Any]] = []

    raw_prs = _fetch_all_prs(owner, repo)

    for pr in raw_prs:
        pr_number = pr["number"]
        pr_id = pr["id"]
        created_at = pr.get("created_at")
        merged_at = pr.get("merged_at")
        # Basic counts
        comments = pr.get("comments", 0)
        review_comments = pr.get("review_comments", 0)
        additions = pr.get("additions", 0)
        deletions = pr.get("deletions", 0)
        changed_files = pr.get("changed_files", 0)

        # CI duration – GitHub does not expose CI time directly via PR API.
        # We approximate with the time between PR creation and merge (if merged).
        ci_duration = None
        if created_at and merged_at:
            # Store as seconds
            ci_duration = (
                pd.to_datetime(merged_at) - pd.to_datetime(created_at)
            ).total_seconds()

        pr_record = {
            "pr_id": pr_id,
            "pr_number": pr_number,
            "repo_owner": owner,
            "repo_name": repo,
            "created_at": created_at,
            "merged_at": merged_at,
            "comments_count": comments,
            "review_comments_count": review_comments,
            "additions": additions,
            "deletions": deletions,
            "changed_files": changed_files,
            "ci_duration_seconds": ci_duration,
        }
        pr_records.append(pr_record)

        # Commit messages (concatenated per PR)
        commits = _fetch_pr_commits(owner, repo, pr_number)
        messages = [c["commit"]["message"] for c in commits if "commit" in c]
        concatenated = "\n---\n".join(messages)
        commit_records.append(
            {"pr_id": pr_id, "commit_message": concatenated}
        )

    pr_df = pd.DataFrame(pr_records)
    commit_df = pd.DataFrame(commit_records)

    # Write parquet files for this repository
    out_path = paths.data("raw", f"{owner}_{repo}.parquet")
    pr_df.to_parquet(out_path, engine="pyarrow", index=False)
    log.info("Wrote PR metadata parquet to %s", out_path)

    # Append commit messages to a global file (handled later)
    return commit_df

def aggregate_commit_messages(commit_dfs: List[pd.DataFrame]) -> None:
    """Combine per‑repo commit message frames and write a single parquet."""
    if not commit_dfs:
        log.warning("No commit messages to aggregate.")
        return
    combined = pd.concat(commit_dfs, ignore_index=True)
    out_path = paths.data("raw", "commit_messages.parquet")
    combined.to_parquet(out_path, engine="pyarrow", index=False)
    log.info("Wrote aggregated commit messages parquet to %s", out_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Entry point for the data acquisition script."""
    parser = None
    try:
        import argparse

        parser = argparse.ArgumentParser(
            description="Stream PR metadata for three high‑star GitHub repos."
        )
        parser.add_argument(
            "--stream",
            action="store_true",
            help="Run the data acquisition (default).",
        )
        args = parser.parse_args()
    except Exception as exc:
        log.error("Argument parsing failed: %s", exc)
        sys.exit(1)

    # The script always runs when invoked directly.
    commit_frames: List[pd.DataFrame] = []
    for owner, repo in REPOS:
        log.info("Processing repository %s/%s", owner, repo)
        commit_df = extract_repository_data(owner, repo)
        commit_frames.append(commit_df)

    aggregate_commit_messages(commit_frames)
    log.info("Data acquisition completed successfully.")

if __name__ == "__main__":
    main()
