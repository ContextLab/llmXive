"""
Fetch Pull Requests from GitHub API for repositories in the config list.
Filters by keywords and saves raw data.
"""
import json
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import sys

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    RATE_LIMIT_HOURLY,
    BACKOFF_INITIAL,
    BACKOFF_MAX,
    STRATIFICATION_SEED
)
from data.logging_config import get_logger
from data.env_config import get_github_token
from data.rate_limiter import create_limiter

logger = get_logger(__name__)

class RepoStats:
    """Helper class to track repository statistics."""
    def __init__(self, repo_id: str, star_count: int):
        self.repo_id = repo_id
        self.star_count = star_count
        self.pr_count = 0
        self.keyword_matches = 0

def load_repo_list(filepath: str) -> List[str]:
    """
    Load repository list from file.
    Handles both 'owner/repo' and 'owner/repo,stars' formats.
    Returns list of 'owner/repo' strings.
    """
    repos = []
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Repo list file not found: {filepath}")

    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Handle potential star count suffix (e.g., "repo,1234")
            parts = line.split(',')
            repo_name = parts[0].strip()
            if '/' in repo_name:
                repos.append(repo_name)
            else:
                logger.warning(f"Skipping invalid repo format: {line}")

    if not repos:
        raise ValueError(f"No valid repositories found in {filepath}")

    logger.info(f"Loaded {len(repos)} repositories from {filepath}")
    return repos

def check_keywords(title: str, body: str, keywords: List[str]) -> bool:
    """
    Check if any of the keywords appear in title or body.
    Case-insensitive search.
    """
    text = f"{title} {body}".lower()
    return any(kw.lower() in text for kw in keywords)

def fetch_prs_for_repo(
    repo_id: str,
    token: str,
    rate_limiter,
    keywords: List[str],
    min_stars: int = 1000
) -> List[Dict[str, Any]]:
    """
    Fetch PRs for a single repository from GitHub API.
    Filters by keywords and returns raw PR data.
    """
    prs = []
    base_url = f"https://api.github.com/repos/{repo_id}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {
        "state": "all",
        "per_page": 100,
        "sort": "created",
        "direction": "desc"
    }

    page = 1
    total_fetched = 0
    max_pages = 10  # Safety limit to prevent excessive API calls

    logger.info(f"Fetching PRs for {repo_id}...")

    while page <= max_pages:
        rate_limiter.wait_if_needed()
        params["page"] = page

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=30)

            if response.status_code == 200:
                page_prs = response.json()
                if not page_prs:
                    break

                for pr in page_prs:
                    # Fetch full PR details to get lines_changed
                    pr_detail_url = pr.get("url")
                    if pr_detail_url:
                        pr_detail_resp = requests.get(pr_detail_url, headers=headers, timeout=30)
                        if pr_detail_resp.status_code == 200:
                            pr_data = pr_detail_resp.json()
                        else:
                            pr_data = pr
                    else:
                        pr_data = pr

                    # Check keywords
                    title = pr_data.get("title", "")
                    body = pr_data.get("body", "")
                    if check_keywords(title, body, keywords):
                        prs.append({
                            "repo": repo_id,
                            "pr_number": pr_data.get("number"),
                            "title": title,
                            "body": body,
                            "created_at": pr_data.get("created_at"),
                            "merged_at": pr_data.get("merged_at"),
                            "author": pr_data.get("user", {}).get("login", "unknown"),
                            "lines_changed": pr_data.get("additions", 0) + pr_data.get("deletions", 0)
                        })
                        total_fetched += 1

                if len(page_prs) < 100:
                    break
                page += 1
            elif response.status_code == 403:
                # Rate limited
                if "rate limit" in response.text.lower():
                    reset_time = int(response.headers.get("X-RateLimit-Reset", 0))
                    wait_time = max(reset_time - int(time.time()) + 1, 60)
                    logger.warning(f"Rate limit hit for {repo_id}. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"API error 403 for {repo_id}: {response.text}")
                    break
            else:
                logger.error(f"API error {response.status_code} for {repo_id}: {response.text}")
                break

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {repo_id}: {e}")
            break

    logger.info(f"Fetched {len(prs)} keyword-matching PRs for {repo_id}")
    return prs

def apply_stratified_sampling(prs: List[Dict], star_bins: Dict[str, int], seed: int) -> List[Dict]:
    """
    Apply stratified sampling based on repository star counts.
    This function is kept for API compatibility but not used in raw fetch.
    """
    # Implementation would go here if sampling was needed at this stage
    return prs

def apply_exclusion_logic(prs: List[Dict], threshold: float) -> List[Dict]:
    """
    Apply exclusion logic based on keyword density.
    This function is kept for API compatibility but not used in raw fetch.
    """
    # Implementation would go here if exclusion was needed at this stage
    return prs

def main():
    """Main entry point for fetching PRs."""
    logger.info("Starting PR fetch process")

    # Load configuration
    token = get_github_token()
    if not token:
        raise EnvironmentError("GitHub token not found. Set GITHUB_TOKEN environment variable.")

    repo_list_path = "data/config/repo_list.txt"
    output_path = "data/raw/prs_raw.json"

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Load repo list
    repos = load_repo_list(repo_list_path)

    # Initialize rate limiter
    rate_limiter = create_limiter(RATE_LIMIT_HOURLY, BACKOFF_INITIAL, BACKOFF_MAX)

    # Keywords to filter by
    keywords = ["copilot", "llm", "generated"]

    all_prs = []

    for repo in repos:
        try:
            prs = fetch_prs_for_repo(repo, token, rate_limiter, keywords)
            all_prs.extend(prs)
        except Exception as e:
            logger.error(f"Failed to process {repo}: {e}")
            continue

    # Save raw data
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_prs, f, indent=2, default=str)

    logger.info(f"Saved {len(all_prs)} PRs to {output_path}")

    return all_prs

if __name__ == "__main__":
    main()
