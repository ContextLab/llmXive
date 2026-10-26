"""
Data acquisition module for the evaluation pipeline.

This implementation streams pull‑request metadata for three verified
GitHub repositories (tensorflow/tensorflow, pytorch/pytorch,
microsoft/vscode) using the GitHub REST API.  It respects rate limits
via exponential back‑off (tenacity) and writes:

* ``data/raw/<owner>_<repo>.parquet`` – one file per repository
  containing PR‑level metadata.
* ``data/raw/commit_messages.parquet`` – a consolidated table with the
  columns ``pr_id`` and ``commit_message`` (the PR title + body).

To stay safely within the unauthenticated GitHub rate‑limit
(60 requests / hour) the script limits the number of PRs fetched per
repository to a very small value when no personal access token is
provided.  If a ``GITHUB_TOKEN`` environment variable is present the
limit is increased because the higher rate‑limit (≈5 000 req/h) permits a
larger sample.

The script has been adjusted to avoid long sleeps on rate‑limit
responses: it now raises a ``RateLimitError`` and lets tenacity handle
the back‑off, preventing the pipeline from timing out.
"""

import os
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
REPOSITORIES = [
    ("tensorflow", "tensorflow"),
    ("pytorch", "pytorch"),
    ("microsoft", "vscode"),
]

# If a personal access token is supplied we can request more PRs;
# otherwise keep the sample tiny to avoid hitting the unauthenticated
# limit (60 requests / hour).
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if GITHUB_TOKEN:
    MAX_PRS = int(os.getenv("DATA_ACQUISITION_MAX_PRS", "20"))
    log.info("GitHub token detected – using larger PR sample")
else:
    # Use a single PR per repo to stay well within rate limits.
    MAX_PRS = int(os.getenv("DATA_ACQUISITION_MAX_PRS", "1"))
    log.info(
        "No GitHub token – limiting PR sample to %d per repository to stay within rate limits",
        MAX_PRS,
    )

API_ROOT = "https://api.github.com"
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
    log.debug("GET %s params=%s", url, params)
    response = requests.get(url, headers=HEADERS, params=params, timeout=15)

    if response.status_code == 403:
        remaining = int(response.headers.get("X-RateLimit-Remaining", "0"))
        reset_ts = int(response.headers.get("X-RateLimit-Reset", "0"))
        if remaining == 0:
            # Do not sleep here; let tenacity handle back‑off.
            log.warning(
                "Rate limit exceeded; will retry after back‑off (reset in %d seconds).",
                max(reset_ts - int(time.time()), 1),
            )
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
            break
        prs.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return prs[:max_prs]

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
        # The following fields are optional; we set them to None to avoid
        # extra API calls that would exhaust the unauthenticated limit.
        "review_comment_count": None,
        "ci_duration_seconds": None,
    }

    # If we have an authenticated token we can afford the extra calls.
    if GITHUB_TOKEN:
        # Review comment count
        try:
            comment_url = f"{API_ROOT}/repos/{owner}/{repo}/pulls/{pr_number}/reviews"
            reviews = _github_get(comment_url, params={"per_page": 100}).json()
            record["review_comment_count"] = len(reviews)
        except Exception as exc:
            log.warning(
                "Failed to fetch review comments for PR %s: %s", pr_number, exc
            )
            record["review_comment_count"] = None

        # CI duration
        try:
            if sha:
                ci_url = f"{API_ROOT}/repos/{owner}/{repo}/commits/{sha}/check-runs"
                runs = _github_get(ci_url, params={"per_page": 100}).json().get(
                    "check_runs", []
                )
                durations = []
                for run in runs:
                    if run.get("status") == "completed":
                        started = run.get("started_at")
                        completed = run.get("completed_at")
                        if started and completed:
                            start_ts = pd.Timestamp(started).timestamp()
                            comp_ts = pd.Timestamp(completed).timestamp()
                            durations.append(comp_ts - start_ts)
                if durations:
                    record["ci_duration_seconds"] = sum(durations) / len(durations)
        except Exception as exc:
            log.warning(
                "Failed to fetch CI duration for PR %s: %s", pr_number, exc
            )
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
        log.info("Fetching PRs for %s/%s", owner, repo)
        try:
            raw_prs = _fetch_all_prs(owner, repo)
        except Exception as exc:
            log.error("Unable to fetch PRs for %s/%s: %s", owner, repo, exc)
            raise

        if not raw_prs:
            log.error("No PRs returned for %s/%s", owner, repo)
            raise RuntimeError(f"No PR data for {owner}/{repo}")

        processed: List[Dict[str, Any]] = []
        for pr in raw_prs:
            try:
                processed.append(_process_pr(owner, repo, pr))
            except Exception as exc:
                log.warning(
                    "Skipping PR %s due to processing error: %s",
                    pr.get("number"),
                    exc,
                )

        df = pd.DataFrame(processed)

        # Write per‑repo parquet
        output_path = paths.data("raw", f"{owner}_{repo}.parquet")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        log.info("Wrote %d rows to %s", len(df), output_path)

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
        "Combined commit messages written to %s (%d rows)",
        commit_path,
        len(commit_df),
    )

if __name__ == "__main__":
    # When executed directly (e.g. via the quick‑start), run the pipeline.
    main()
