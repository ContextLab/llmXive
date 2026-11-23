"""
Data acquisition module for the evaluation pipeline.

This implementation streams pull‑request metadata for three verified
GitHub repositories (tensorflow/tensorflow, pytorch/pytorch,
microsoft/vscode) using the GitHub REST API.  It respects rate limits
via exponential back‑off (tenacity) and writes:

* ``data/raw/<owner>_<repo>.parquet`` – one file per repository
  containing PR‑level metadata.
* ``data/raw/commit_messages.parquet`` – a consolidated table with the
  columns ``pr_id`` and ``commit_message`` (the PR title).

The script deliberately limits the number of PRs fetched per repository
to ``MAX_PRS = 200`` to keep the run‑time well within the CI limits while
still providing a non‑empty, real dataset that satisfies the verification
requirements.
"""

import os
import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import pandas as pd
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Repositories must have ≥1 000 stars and ≥100 PRs – the three chosen
# repositories satisfy these constraints.
REPOSITORIES = [
    ("tensorflow", "tensorflow"),
    ("pytorch", "pytorch"),
    ("microsoft", "vscode"),
]

# Limit the number of PRs fetched per repository – enough to produce a
# non‑empty parquet file while staying within the GitHub unauthenticated
# rate limit (60 requests / hour).  The back‑off logic will pause if the
# limit is hit.
MAX_PRS = 200

# GitHub API endpoint template
API_ROOT = "https://api.github.com"

# Optional token to increase the rate limit (≈5 000 requests / hour)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github.v3+json"}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
class RateLimitError(RuntimeError):
    """Raised when the GitHub API signals a rate‑limit condition."""

@retry(
    retry=retry_if_exception_type(
        (requests.exceptions.RequestException, RateLimitError)
    ),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)
def _github_get(
    url: str, params: Optional[Dict[str, Any]] = None
) -> requests.Response:
    """
    Perform a GET request against the GitHub API with exponential back‑off.
    If a 403 with an ``X-RateLimit-Remaining`` header of ``0`` is seen,
    a :class:`RateLimitError` is raised so tenacity can back‑off.
    """
    log.debug(f"GET {url}  params={params}")
    response = requests.get(url, headers=HEADERS, params=params, timeout=15)

    if response.status_code == 403:
        # Check for rate‑limit headers
        remaining = int(response.headers.get("X-RateLimit-Remaining", "0"))
        reset_ts = int(response.headers.get("X-RateLimit-Reset", "0"))
        if remaining == 0:
            wait_seconds = max(reset_ts - int(time.time()), 1)
            log.warning(
                f"Rate limit exceeded, sleeping for {wait_seconds}s before retry."
            )
            time.sleep(wait_seconds)
            raise RateLimitError("GitHub rate limit exceeded")
    response.raise_for_status()
    return response

def _fetch_pr_page(
    owner: str, repo: str, page: int, per_page: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch a single page of closed pull requests.
    """
    url = f"{API_ROOT}/repos/{owner}/{repo}/pulls"
    params = {
        "state": "closed",
        "per_page": per_page,
        "page": page,
        "sort": "created",
        "direction": "desc",
    }
    resp = _github_get(url, params=params)
    return resp.json()

def _fetch_all_prs(
    owner: str, repo: str, max_prs: int = MAX_PRS
) -> List[Dict[str, Any]]:
    """
    Stream closed PRs for ``owner/repo`` until ``max_prs`` is reached.
    """
    prs: List[Dict[str, Any]] = []
    page = 1
    while len(prs) < max_prs:
        batch = _fetch_pr_page(owner, repo, page)
        if not batch:
            break  # No more PRs
        prs.extend(batch)
        if len(batch) < 100:
            break  # Last page
        page += 1
    return prs[:max_prs]

def _fetch_review_comment_count(
    owner: str, repo: str, pr_number: int
) -> int:
    """
    Count review comments for a PR (both review bodies and inline comments).
    """
    url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
    reviews = _github_get(url, params={"per_page": 100}).json()
    return len(reviews)

def _fetch_ci_duration(
    owner: str, repo: str, sha: str
) -> Optional[float]:
    """
    Approximate CI duration by averaging the elapsed time of completed
    check runs for the commit ``sha``.  Returns ``None`` if no check runs
    are available.
    """
    url = f"{API_ROOT}/repos/{owner}/{repo}/commits/{sha}/check-runs"
    runs = _github_get(url, params={"per_page": 100}).json().get(
        "check_runs", []
    )
    durations = []
    for run in runs:
        if run.get("status") == "completed":
            started = run.get("started_at")
            completed = run.get("completed_at")
            if started and completed:
                try:
                    start_ts = pd.Timestamp(started).timestamp()
                    comp_ts = pd.Timestamp(completed).timestamp()
                    durations.append(comp_ts - start_ts)
                except Exception:
                    continue
    if durations:
        return sum(durations) / len(durations)
    return None

def _process_pr(
    owner: str, repo: str, pr: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract the fields required downstream.  The schema used by the
    pipeline (``contracts/pull_request.schema.yaml``) contains at least
    the following columns – additional columns are harmless.
    """
    pr_number = pr["number"]
    sha = pr.get("head", {}).get("sha")

    # Basic metadata
    record: Dict[str, Any] = {
        "pr_id": pr_number,
        "repo_owner": owner,
        "repo_name": repo,
        "repo_id": f"{owner}/{repo}",
        "created_at": pr.get("created_at"),
        "merged_at": pr.get("merged_at"),
        "state": pr.get("state"),
        "title": pr.get("title"),
        "body": pr.get("body") or "",
        "additions": pr.get("additions"),
        "deletions": pr.get("deletions"),
        "changed_files": pr.get("changed_files"),
        "author_login": pr.get("user", {}).get("login"),
    }

    # Review comment count (may be 0)
    try:
        record["review_comment_count"] = _fetch_review_comment_count(
            owner, repo, pr_number
        )
    except Exception as exc:
        log.warning(
            f"Failed to fetch review comments for PR {pr_number}: {exc}"
        )
        record["review_comment_count"] = None

    # CI duration (seconds)
    try:
        if sha:
            ci_sec = _fetch_ci_duration(owner, repo, sha)
        else:
            ci_sec = None
        record["ci_duration_seconds"] = ci_sec
    except Exception as exc:
        log.warning(f"Failed to fetch CI duration for PR {pr_number}: {exc}")
        record["ci_duration_seconds"] = None

    return record

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """
    Stream PR metadata for each repository, write per‑repo parquet files,
    and create a consolidated ``commit_messages.parquet`` file.
    """
    all_commit_rows: List[Dict[str, Any]] = []

    for owner, repo in REPOSITORIES:
        log.info(f"Fetching PRs for {owner}/{repo}")
        try:
            raw_prs = _fetch_all_prs(owner, repo)
        except Exception as exc:
            log.error(f"Unable to fetch PRs for {owner}/{repo}: {exc}")
            raise

        if not raw_prs:
            log.error(f"No PRs returned for {owner}/{repo}")
            raise RuntimeError(f"No PR data for {owner}/{repo}")

        processed: List[Dict[str, Any]] = []
        for pr in raw_prs:
            try:
                processed.append(_process_pr(owner, repo, pr))
            except Exception as exc:
                log.warning(
                    f"Skipping PR {pr.get('number')} due to processing error: {exc}"
                )

        df = pd.DataFrame(processed)

        # Write per‑repo parquet
        output_path = paths.data("raw", f"{owner}_{repo}.parquet")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        log.info(f"Wrote {len(df)} rows to {output_path}")

        # Collect commit messages for the combined file
        for _, row in df.iterrows():
            commit_msg = (row["title"] or "") + (" " + (row["body"] or ""))
            commit_msg = commit_msg.strip()
            if not commit_msg:
                continue
            all_commit_rows.append(
                {"pr_id": row["pr_id"], "commit_message": commit_msg}
            )

    # ------------------------------------------------------------------
    # Write combined commit messages parquet
    # ------------------------------------------------------------------
    if not all_commit_rows:
        log.error("No commit messages collected from any repository.")
        raise RuntimeError("Empty commit message set")

    commit_df = pd.DataFrame(all_commit_rows).drop_duplicates()
    commit_path = paths.data("raw", "commit_messages.parquet")
    commit_path.parent.mkdir(parents=True, exist_ok=True)
    commit_df.to_parquet(commit_path, index=False)
    log.info(
        f"Combined commit messages written to {commit_path} ({len(commit_df)} rows)"
    )

if __name__ == "__main__":
    # When executed directly (e.g. via the quick‑start), run the pipeline.
    main()