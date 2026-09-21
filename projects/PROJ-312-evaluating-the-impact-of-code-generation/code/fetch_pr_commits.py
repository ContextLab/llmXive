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

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    logger.warning("GITHUB_TOKEN not set. API calls may be rate-limited.")

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "llmXive-Pipeline",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

def load_repos(repos_path: str = "data/raw/repos.json") -> List[Dict[str, Any]]:
    """Load the list of repositories fetched in T012a."""
    if not os.path.exists(repos_path):
        raise FileNotFoundError(f"Repository list not found at {repos_path}. Run T012a first.")
    with open(repos_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"Loaded {len(data)} repositories from {repos_path}")
    return data

def fetch_prs_for_repo(repo_full_name: str, per_page: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch ALL pull requests for a given repository, handling pagination via the 'Link' header.
    Only fetches merged PRs (state=merged) to ensure turnaround time is calculable.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/pulls"
    params = {
        "state": "merged",
        "per_page": per_page,
        "sort": "created",
        "direction": "asc",
    }

    all_prs = []
    page = 1

    logger.info(f"Fetching PRs for {repo_full_name}...")

    while True:
        params["page"] = page
        try:
            response = api_request_with_backoff(url, headers=HEADERS, params=params)
            log_api_headers(response)

            if response.status_code != 200:
                logger.error(f"Failed to fetch PRs for {repo_full_name}: {response.status_code} - {response.text}")
                break

            prs = response.json()
            if not prs:
                break

            all_prs.extend(prs)
            logger.info(f"Fetched page {page} ({len(prs)} PRs) for {repo_full_name}. Total so far: {len(all_prs)}")

            # Check for next page in Link header
            link_header = response.headers.get("Link")
            if not link_header or 'rel="next"' not in link_header:
                break

            # Parse next URL from Link header
            # Format: <url>; rel="next", <url>; rel="last"
            next_url = None
            for link in link_header.split(","):
                parts = link.strip().split(";")
                if len(parts) >= 2 and 'rel="next"' in parts[1]:
                    next_url = parts[0].strip().strip("<>")
                    break

            if next_url:
                # Use the full next_url to preserve pagination params
                response = api_request_with_backoff(next_url, headers=HEADERS)
                log_api_headers(response)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch next page for {repo_full_name}: {response.status_code}")
                    break
                prs = response.json()
                if not prs:
                    break
                all_prs.extend(prs)
                # We don't increment page here because we are following the Link header directly
                # But we need to ensure we don't loop infinitely if Link header is malformed
                # We rely on the empty list check and Link header presence
            else:
                break

            # Small delay to be polite to the API
            time.sleep(1)
            page += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching PRs for {repo_full_name}: {e}")
            break

    logger.info(f"Total PRs fetched for {repo_full_name}: {len(all_prs)}")
    return all_prs

def fetch_commits_for_pr(repo_full_name: str, pr_number: int) -> List[Dict[str, Any]]:
    """
    Fetch ALL commits for a specific PR, handling pagination via the 'Link' header.
    Returns a list of commit objects containing the message.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/pulls/{pr_number}/commits"
    params = {"per_page": 100}

    all_commits = []
    page = 1

    while True:
        params["page"] = page
        try:
            response = api_request_with_backoff(url, headers=HEADERS, params=params)
            log_api_headers(response)

            if response.status_code != 200:
                logger.error(f"Failed to fetch commits for PR #{pr_number} in {repo_full_name}: {response.status_code}")
                break

            commits = response.json()
            if not commits:
                break

            all_commits.extend(commits)
            logger.debug(f"Fetched page {page} ({len(commits)} commits) for PR #{pr_number}")

            # Check for next page in Link header
            link_header = response.headers.get("Link")
            if not link_header or 'rel="next"' not in link_header:
                break

            # Parse next URL from Link header
            next_url = None
            for link in link_header.split(","):
                parts = link.strip().split(";")
                if len(parts) >= 2 and 'rel="next"' in parts[1]:
                    next_url = parts[0].strip().strip("<>")
                    break

            if next_url:
                response = api_request_with_backoff(next_url, headers=HEADERS)
                log_api_headers(response)
                if response.status_code != 200:
                    logger.error(f"Failed to fetch next page for PR #{pr_number}: {response.status_code}")
                    break
                commits = response.json()
                if not commits:
                    break
                all_commits.extend(commits)
            else:
                break

            time.sleep(1)
            page += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching commits for PR #{pr_number}: {e}")
            break

    return all_commits

def parse_iso_datetime(iso_str: str) -> datetime:
    """Parse ISO 8601 datetime string."""
    if not iso_str:
        return None
    # Handle 'Z' suffix and timezone offsets
    iso_str = iso_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(iso_str)
    except ValueError:
        # Fallback for older Python versions or weird formats
        return datetime.strptime(iso_str[:19], "%Y-%m-%dT%H:%M:%S")

def calculate_turnaround_hours(created_at: str, merged_at: str) -> float:
    """Calculate turnaround time in hours between created_at and merged_at."""
    if not created_at or not merged_at:
        return None
    created = parse_iso_datetime(created_at)
    merged = parse_iso_datetime(merged_at)
    if not created or not merged:
        return None
    delta = merged - created
    return delta.total_seconds() / 3600.0

def extract_commit_messages(commits: List[Dict[str, Any]]) -> List[str]:
    """Extract commit messages from a list of commit objects."""
    messages = []
    for commit in commits:
        commit_data = commit.get("commit", {})
        message = commit_data.get("message", "")
        if message:
            messages.append(message)
    return messages

def process_pr_data(repo_name: str, pr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single PR: fetch commits, extract messages, calculate turnaround.
    Returns a dictionary with PR metadata and commit messages, or None if invalid.
    """
    pr_id = str(pr.get("number"))
    created_at = pr.get("created_at")
    merged_at = pr.get("merged_at")

    if not merged_at:
        # Should be filtered out by fetch_prs_for_repo (state=merged), but double check
        logger.debug(f"Skipping PR {pr_id} in {repo_name} due to missing merged_at")
        return None

    turnaround = calculate_turnaround_hours(created_at, merged_at)
    if turnaround is None:
        logger.warning(f"Could not calculate turnaround for PR {pr_id} in {repo_name}")
        return None

    # Fetch all commits for this PR
    commits = fetch_commits_for_pr(repo_name, int(pr_id))
    messages = extract_commit_messages(commits)

    return {
        "pr_id": pr_id,
        "repo_name": repo_name,
        "created_at": created_at,
        "merged_at": merged_at,
        "turnaround_hours": turnaround,
        "commit_messages": messages,
        "labels": [label["name"] for label in pr.get("labels", [])],
        "author": pr.get("user", {}).get("login"),
    }

def main():
    """
    Main entry point for T012b:
    1. Load repos from T012a.
    2. For each repo, fetch ALL PRs.
    3. For each PR, fetch ALL commits.
    4. Save raw PR data with commit messages to data/raw/pr_data.json.
    """
    logger.info("Starting T012b: Fetching PRs and all commits with pagination")

    repos = load_repos()
    if not repos:
        logger.error("No repositories found. Exiting.")
        return

    all_pr_data = []
    processed_repos = 0
    skipped_repos = []

    for repo in repos:
        repo_name = repo.get("name")
        if not repo_name:
            continue

        logger.info(f"Processing repository: {repo_name}")
        try:
            prs = fetch_prs_for_repo(repo_name)
            
            # T014 logic: Skip repos with < 50 PRs
            if len(prs) < 50:
                logger.warning(f"Skipping {repo_name} with only {len(prs)} PRs (< 50 threshold)")
                skipped_repos.append(repo_name)
                continue

            repo_pr_data = []
            for pr in prs:
                pr_result = process_pr_data(repo_name, pr)
                if pr_result:
                    repo_pr_data.append(pr_result)
            
            all_pr_data.extend(repo_pr_data)
            processed_repos += 1
            logger.info(f"Successfully processed {repo_name}: {len(repo_pr_data)} PRs")

        except Exception as e:
            logger.error(f"Error processing {repo_name}: {e}", exc_info=True)
            continue

    # Save raw PR data
    output_path = "data/raw/pr_data.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_pr_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved raw PR data to {output_path} ({len(all_pr_data)} PRs)")

    # Save excluded repos list
    if skipped_repos:
        excluded_path = "data/processed/excluded_repos.txt"
        os.makedirs(os.path.dirname(excluded_path), exist_ok=True)
        with open(excluded_path, "w", encoding="utf-8") as f:
            for repo in skipped_repos:
                f.write(f"{repo}\n")
        logger.info(f"Saved excluded repos to {excluded_path}")

    logger.info("T012b completed successfully.")

if __name__ == "__main__":
    main()