"""
Module: fetch_pr_commits.py
Implements T012b: Fetch PRs and iterate through commits with pagination handling.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

from utils import api_request_with_backoff, log_api_headers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_PRS_PER_REPO = 500  # Representative number of PRs per repo
MAX_TOTAL_PRS = 2000    # Substantial threshold for cumulative dataset size
COMMITS_PER_PR_LIMIT = 100  # Fetch up to N commits per PR to manage size
GITHUB_API_BASE = "https://api.github.com"


def load_repos(repos_path: Path) -> List[Dict[str, Any]]:
    """Load the list of repositories from T012a output."""
    if not repos_path.exists():
        logger.error(f"Repos file not found: {repos_path}")
        return []
    with open(repos_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def fetch_prs_for_repo(repo_name: str, token: str) -> List[Dict[str, Any]]:
    """
    Fetch PRs for a specific repository using GitHub API.
    Handles pagination via the 'Link' header.
    """
    prs = []
    page = 1
    per_page = 100
    total_fetched = 0

    base_url = f"{GITHUB_API_BASE}/repos/{repo_name}/pulls"

    logger.info(f"Fetching PRs for {repo_name} (limit: {MAX_PRS_PER_REPO})")

    while total_fetched < MAX_PRS_PER_REPO:
        params = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": per_page,
            "page": page,
        }

        # Use the backoff wrapper to handle rate limits
        response = api_request_with_backoff(base_url, token, params)

        if response is None:
            logger.error(f"Failed to fetch PRs for {repo_name} after retries.")
            break

        log_api_headers(response)

        page_data = response.json()
        if not page_data:
            break  # No more pages

        prs.extend(page_data)
        total_fetched += len(page_data)
        page += 1

        # Check if we hit the repo limit
        if total_fetched >= MAX_PRS_PER_REPO:
            logger.info(f"Reached PR limit for {repo_name}: {total_fetched}")
            break

        # Check Link header for next page
        link_header = response.headers.get("Link")
        if not link_header or "rel=\"next\"" not in link_header:
            break

        # Small delay to respect rate limits
        time.sleep(0.5)

    logger.info(f"Fetched {len(prs)} PRs for {repo_name}")
    return prs[:MAX_PRS_PER_REPO]


def fetch_commits_for_pr(repo_name: str, pr_number: int, token: str) -> List[Dict[str, Any]]:
    """
    Fetch commits for a specific PR.
    Handles pagination.
    """
    commits = []
    page = 1
    per_page = 100
    total_fetched = 0

    base_url = f"{GITHUB_API_BASE}/repos/{repo_name}/pulls/{pr_number}/commits"

    while total_fetched < COMMITS_PER_PR_LIMIT:
        params = {
            "per_page": per_page,
            "page": page,
        }

        response = api_request_with_backoff(base_url, token, params)

        if response is None:
            logger.warning(f"Failed to fetch commits for PR #{pr_number} in {repo_name}")
            break

        log_api_headers(response)

        page_data = response.json()
        if not page_data:
            break

        commits.extend(page_data)
        total_fetched += len(page_data)
        page += 1

        # Check Link header
        link_header = response.headers.get("Link")
        if not link_header or "rel=\"next\"" not in link_header:
            break

        time.sleep(0.5)

    logger.debug(f"Fetched {len(commits)} commits for PR #{pr_number}")
    return commits[:COMMITS_PER_PR_LIMIT]


def parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string."""
    if not iso_str:
        return None
    try:
        # Handle common variations
        iso_str = iso_str.replace("Z", "+00:00")
        if "+00:00" in iso_str:
            # Python 3.7+ handles this directly, but some parsers prefer standard
            pass
        return datetime.fromisoformat(iso_str)
    except ValueError as e:
        logger.warning(f"Failed to parse date {iso_str}: {e}")
        return None


def calculate_turnaround_hours(created_at: datetime, merged_at: datetime) -> Optional[float]:
    """Calculate turnaround time in hours."""
    if not created_at or not merged_at:
        return None
    delta = merged_at - created_at
    return delta.total_seconds() / 3600.0


def extract_commit_messages(commits: List[Dict[str, Any]]) -> List[str]:
    """Extract commit messages from the commits list."""
    messages = []
    for commit in commits:
        if "commit" in commit and "message" in commit["commit"]:
            messages.append(commit["commit"]["message"])
    return messages


def process_pr_data(
    repo_name: str,
    pr_data: Dict[str, Any],
    token: str
) -> Optional[Dict[str, Any]]:
    """
    Process a single PR: fetch commits, extract messages, calculate turnaround.
    Returns a structured data object or None if failed.
    """
    pr_id = pr_data.get("id")
    pr_number = pr_data.get("number")
    created_at_str = pr_data.get("created_at")
    merged_at_str = pr_data.get("merged_at")
    labels = pr_data.get("labels", [])

    # Skip if merged_at is missing (T013 logic)
    if not merged_at_str:
        return None

    created_at = parse_iso_datetime(created_at_str)
    merged_at = parse_iso_datetime(merged_at_str)

    turnaround_hours = calculate_turnaround_hours(created_at, merged_at)
    if turnaround_hours is None:
        return None

    # Fetch commits for this PR
    commits = fetch_commits_for_pr(repo_name, pr_number, token)
    commit_messages = extract_commit_messages(commits)

    return {
        "pr_id": str(pr_id),
        "repo_name": repo_name,
        "pr_number": pr_number,
        "created_at": created_at_str,
        "merged_at": merged_at_str,
        "turnaround_hours": turnaround_hours,
        "labels": [label["name"] for label in labels],
        "commit_messages": commit_messages,
        "commit_count": len(commits),
    }


def main():
    """
    Main entry point for T012b.
    Iterates through repos from T012a, fetches PRs, fetches commits,
    and saves the raw data.
    """
    base_path = Path("projects/PROJ-312-evaluating-the-impact-of-code-generation")
    repos_path = base_path / "data/raw/repos.json"
    output_path = base_path / "data/raw/pr_data.json"

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN environment variable not set.")
        return

    logger.info("Starting T012b: Fetching PRs and Commits")

    repos = load_repos(repos_path)
    if not repos:
        logger.error("No repositories loaded.")
        return

    all_pr_data = []
    total_prs_processed = 0

    for repo in repos:
        repo_name = repo.get("name")
        if not repo_name:
            continue

        # Check cumulative limit
        if total_prs_processed >= MAX_TOTAL_PRS:
            logger.info(f"Cumulative PR limit ({MAX_TOTAL_PRS}) reached. Stopping.")
            break

        try:
            prs = fetch_prs_for_repo(repo_name, token)
            if not prs:
                continue

            for pr in prs:
                # Check cumulative limit again
                if total_prs_processed >= MAX_TOTAL_PRS:
                    break

                processed = process_pr_data(repo_name, pr, token)
                if processed:
                    all_pr_data.append(processed)
                    total_prs_processed += 1

            logger.info(f"Processed {repo_name}. Total PRs so far: {total_prs_processed}")

        except Exception as e:
            logger.error(f"Error processing {repo_name}: {e}", exc_info=True)
            continue

    # Save output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_pr_data, f, indent=2, default=str)

    logger.info(f"Saved {len(all_pr_data)} PR records to {output_path}")


if __name__ == "__main__":
    main()
