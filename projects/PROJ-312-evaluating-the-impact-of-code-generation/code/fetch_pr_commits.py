import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests

from utils import api_request_with_backoff, log_api_headers

# Constants
MAX_PAGES_PER_REPO = 50
MAX_EXECUTION_TIME_SECONDS = 1800  # 30 minutes
BASE_URL = "https://api.github.com"

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.FileHandler('logs/pipeline.log')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

def load_repos(repos_path: str) -> List[Dict[str, Any]]:
    """Load the list of repositories from the raw data file."""
    if not os.path.exists(repos_path):
        logger.error(f"Repos file not found: {repos_path}")
        raise FileNotFoundError(f"Repos file not found: {repos_path}")
    
    with open(repos_path, 'r') as f:
        return json.load(f)

def parse_iso_datetime(iso_str: str) -> datetime:
    """Parse ISO 8601 datetime string."""
    if not iso_str:
        return None
    # Handle 'Z' suffix and standard ISO format
    iso_str = iso_str.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(iso_str)
    except ValueError:
        # Fallback for formats without timezone info if necessary
        return datetime.fromisoformat(iso_str.replace('+00:00', ''))

def calculate_turnaround_hours(created_at: str, merged_at: str) -> Optional[float]:
    """Calculate turnaround time in hours."""
    if not created_at or not merged_at:
        return None
    created = parse_iso_datetime(created_at)
    merged = parse_iso_datetime(merged_at)
    if not created or not merged:
        return None
    delta = merged - created
    return delta.total_seconds() / 3600

def fetch_prs_for_repo(repo_name: str, token: Optional[str] = None) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Fetch PRs for a specific repository with pagination.
    Returns (list of PRs, truncated_flag).
    Truncated_flag is True if MAX_PAGES_PER_REPO was reached.
    """
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'llmXive-Pipeline'
    }
    if token:
        headers['Authorization'] = f'token {token}'

    url = f"{BASE_URL}/repos/{repo_name}/pulls"
    params = {
        'state': 'all',
        'per_page': 100,
        'sort': 'created',
        'direction': 'asc'
    }

    all_prs = []
    page = 1
    truncated = False
    start_time = time.time()

    while True:
        # Check time budget
        if time.time() - start_time > MAX_EXECUTION_TIME_SECONDS:
            logger.warning(f"Time budget exceeded for {repo_name}. Stopping pagination.")
            truncated = True
            break

        if page > MAX_PAGES_PER_REPO:
            logger.warning(f"Max pages ({MAX_PAGES_PER_REPO}) reached for {repo_name}. Stopping pagination.")
            truncated = True
            break

        params['page'] = page
        logger.info(f"Fetching page {page} for {repo_name}...")

        try:
            response = api_request_with_backoff(url, headers, params=params)
            log_api_headers(response, {'retry_count': 0}) # Log headers from the successful request

            if response.status_code == 200:
                prs = response.json()
                if not prs:
                    break  # No more results
                all_prs.extend(prs)
                
                # Check Link header for next page
                link_header = response.headers.get('Link', '')
                if 'rel="next"' not in link_header:
                    break # No more pages
                
                page += 1
            elif response.status_code == 404:
                logger.warning(f"Repo {repo_name} not found or no PRs accessible.")
                break
            elif response.status_code == 403:
                if 'rate limit' in response.text.lower():
                    logger.error(f"Rate limit exceeded for {repo_name}.")
                    truncated = True
                    break
                else:
                    logger.warning(f"Access forbidden for {repo_name}.")
                    break
            else:
                logger.error(f"Unexpected status code {response.status_code} for {repo_name}.")
                break
        except Exception as e:
            logger.error(f"Error fetching page {page} for {repo_name}: {e}")
            break

    return all_prs, truncated

def fetch_commits_for_pr(pr_number: int, repo_name: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch commits for a specific PR."""
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'llmXive-Pipeline'
    }
    if token:
        headers['Authorization'] = f'token {token}'

    url = f"{BASE_URL}/repos/{repo_name}/pulls/{pr_number}/commits"
    
    try:
        response = api_request_with_backoff(url, headers)
        log_api_headers(response, {'retry_count': 0})

        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Failed to fetch commits for PR #{pr_number} in {repo_name}: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error fetching commits for PR #{pr_number}: {e}")
        return []

def extract_commit_messages(commits: List[Dict[str, Any]]) -> List[str]:
    """Extract commit messages from the list of commit objects."""
    messages = []
    for commit in commits:
        commit_data = commit.get('commit', {})
        message = commit_data.get('message', '')
        if message:
            messages.append(message)
    return messages

def process_pr_data(pr: Dict[str, Any], commits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process a single PR and its commits into a standardized record."""
    repo_name = pr.get('base', {}).get('repo', {}).get('full_name', '')
    pr_id = str(pr.get('number', ''))
    created_at = pr.get('created_at')
    merged_at = pr.get('merged_at')
    
    turnaround = calculate_turnaround_hours(created_at, merged_at)
    commit_messages = extract_commit_messages(commits)
    
    return {
        'repo_name': repo_name,
        'pr_id': pr_id,
        'created_at': created_at,
        'merged_at': merged_at,
        'turnaround_hours': turnaround,
        'commit_messages': commit_messages,
        'labels': [label.get('name') for label in pr.get('labels', [])],
        'state': pr.get('state')
    }

def fetch_prs_and_commits_for_repos(repos: List[Dict[str, Any]], token: Optional[str] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Iterate through repos, fetching PRs and their commits.
    Returns (list of processed PR records, list of truncated repo names).
    """
    all_records = []
    truncated_repos = []
    start_time = time.time()

    for repo in repos:
        # Check global time budget
        if time.time() - start_time > MAX_EXECUTION_TIME_SECONDS:
            logger.warning("Global time budget exceeded. Stopping fetch.")
            break

        repo_name = repo.get('name') or repo.get('full_name')
        if not repo_name:
            continue

        logger.info(f"Processing repository: {repo_name}")
        
        prs, truncated = fetch_prs_for_repo(repo_name, token)
        
        if truncated:
            truncated_repos.append(repo_name)
            logger.warning(f"Data for {repo_name} may be incomplete.")

        for pr in prs:
            # Skip open/unmerged PRs if we strictly need turnaround time (merged_at required)
            # However, the task says "Fetch ALL PRs", but turnaround calculation requires merged_at.
            # We will process them, but turnaround will be None for unmerged ones.
            pr_number = pr.get('number')
            if not pr_number:
                continue

            commits = fetch_commits_for_pr(pr_number, repo_name, token)
            record = process_pr_data(pr, commits)
            all_records.append(record)

    return all_records, truncated_repos

def save_excluded_repos(truncated_repos: List[str], output_path: str):
    """Save the list of truncated repos to a text file."""
    with open(output_path, 'w') as f:
        for repo in truncated_repos:
            f.write(f"{repo}\n")
    logger.info(f"Saved truncated repos to {output_path}")

def save_raw_pr_data(records: List[Dict[str, Any]], output_path: str):
    """Save raw PR data to JSON."""
    with open(output_path, 'w') as f:
        json.dump(records, f, indent=2)
    logger.info(f"Saved raw PR data to {output_path}")

def main():
    """Main entry point for T012b."""
    # Paths
    repos_path = "data/raw/repos.json"
    output_path = "data/processed/pr_turnaround_partial.csv" # Task specifies partial CSV for truncated
    truncated_log_path = "data/processed/truncated_repos.txt"
    
    # Ensure output directory exists
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    # Load repos
    try:
        repos = load_repos(repos_path)
        logger.info(f"Loaded {len(repos)} repositories.")
    except Exception as e:
        logger.error(f"Failed to load repos: {e}")
        return

    # Fetch data
    # Note: In a real pipeline, the token would be passed or loaded from env.
    # For this script to run, we assume the environment is configured or token is None (public data).
    records, truncated_repos = fetch_prs_and_commits_for_repos(repos)

    logger.info(f"Fetched {len(records)} PR records.")
    if truncated_repos:
        logger.warning(f"Truncated repos: {truncated_repos}")
        save_excluded_repos(truncated_repos, truncated_log_path)

    # Save partial data if truncation occurred, otherwise full data
    # The task says: "If the stop condition triggers, save partial data to ...partial.csv"
    # If no truncation, we should ideally save to the main file, but the task specifically 
    # asks for the partial file handling logic here. 
    # To be safe and follow the instruction literally for this task:
    if truncated_repos:
        save_raw_pr_data(records, output_path)
    else:
        # If no truncation, we still save the data. The main pipeline T018b will handle the final CSV.
        # We save to a temp name or the same name to ensure data exists.
        save_raw_pr_data(records, "data/processed/pr_turnaround_full_temp.json")
        logger.info("No truncation occurred. Data saved to full_temp.json.")

    logger.info("T012b execution complete.")

if __name__ == "__main__":
    main()