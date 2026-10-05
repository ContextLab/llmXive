import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import requests

# Import utilities from utils module
from utils import api_request_with_backoff, log_api_headers, MIN_PR_THRESHOLD

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GITHUB_API_BASE = "https://api.github.com"
DEFAULT_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "llmXive-research-agent"
}

def parse_iso_datetime(iso_string: str) -> datetime:
    """Parse ISO 8601 datetime string to datetime object."""
    if not iso_string:
        return None
    # Handle 'Z' suffix and timezone offsets
    iso_string = iso_string.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(iso_string)
    except ValueError:
        # Fallback for older Python versions or strict formats
        return datetime.strptime(iso_string[:19], "%Y-%m-%dT%H:%M:%S")

def extract_commit_keywords(commit_messages: List[str]) -> bool:
    """
    Check if any commit message contains AI-related keywords.
    Keywords: 'copilot', 'ai-generated', 'ai-assisted', 'llm'
    """
    keywords = ['copilot', 'ai-generated', 'ai-assisted', 'llm', 'github copilot']
    for msg in commit_messages:
        msg_lower = msg.lower()
        if any(kw in msg_lower for kw in keywords):
            return True
    return False

def check_labels(labels: List[str]) -> bool:
    """
    Check if any label indicates AI assistance.
    Labels: 'ai-generated', 'copilot-assisted', 'llm-code'
    """
    ai_labels = ['ai-generated', 'copilot-assisted', 'llm-code']
    for label in labels:
        if label.lower() in ai_labels:
            return True
    return False

def classify_pr(pr_data: Dict[str, Any]) -> str:
    """
    Classify a PR as 'AI-assisted' or 'Non-AI' based on commit messages and labels.
    """
    commit_messages = pr_data.get('commit_messages', [])
    labels = pr_data.get('labels', [])

    if extract_commit_keywords(commit_messages) or check_labels(labels):
        return 'AI-assisted'
    return 'Non-AI'

def calculate_turnaround_hours(created_at: str, merged_at: str) -> float:
    """Calculate turnaround time in hours between creation and merge."""
    created = parse_iso_datetime(created_at)
    merged = parse_iso_datetime(merged_at)

    if not created or not merged:
        return None

    delta = merged - created
    return delta.total_seconds() / 3600.0

def fetch_repos_from_github(language: str, min_stars: int = 10000, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch top repositories by star count for a given language.
    """
    url = f"{GITHUB_API_BASE}/search/repositories"
    params = {
        "q": f"language:{language} stars:>{min_stars}",
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    }
    headers = DEFAULT_HEADERS.copy()

    try:
        response = api_request_with_backoff(url, headers)
        log_api_headers(response)

        if response.status_code != 200:
            logger.error(f"Failed to fetch repos for {language}: {response.status_code}")
            return []

        data = response.json()
        items = data.get('items', [])
        repos = []
        for item in items:
            repos.append({
                "name": item['full_name'],
                "stars": item['stargazers_count'],
                "url": item['html_url']
            })
        return repos
    except Exception as e:
        logger.error(f"Error fetching repos for {language}: {e}")
        return []

def fetch_prs_for_repo(repo_name: str, page: int = 1, per_page: int = 100) -> Tuple[List[Dict], Optional[str]]:
    """
    Fetch PRs for a specific repository with pagination.
    Returns a tuple of (pr_list, next_page_url).
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/pulls"
    params = {
        "state": "all",
        "per_page": per_page,
        "page": page
    }
    headers = DEFAULT_HEADERS.copy()

    try:
        response = api_request_with_backoff(url, headers)
        log_api_headers(response)

        if response.status_code != 200:
            logger.error(f"Failed to fetch PRs for {repo_name} (page {page}): {response.status_code}")
            return [], None

        data = response.json()
        links = response.links
        next_url = links.get('next', {}).get('url') if links else None
        return data, next_url
    except Exception as e:
        logger.error(f"Error fetching PRs for {repo_name}: {e}")
        return [], None

def fetch_commits_for_pr(repo_name: str, pr_number: int) -> List[str]:
    """
    Fetch commit messages for a specific PR.
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/pulls/{pr_number}/commits"
    headers = DEFAULT_HEADERS.copy()

    try:
        response = api_request_with_backoff(url, headers)
        log_api_headers(response)

        if response.status_code != 200:
            logger.warning(f"Failed to fetch commits for PR #{pr_number}: {response.status_code}")
            return []

        data = response.json()
        messages = [commit['commit']['message'] for commit in data]
        return messages
    except Exception as e:
        logger.error(f"Error fetching commits for PR #{pr_number}: {e}")
        return []

def process_pr_data(repo_name: str, pr_list: List[Dict]) -> List[Dict]:
    """
    Process a list of PRs: filter, classify, and calculate turnaround.
    """
    processed = []
    excluded_count = 0

    for pr in pr_list:
        # Skip unmerged PRs
        if not pr.get('merged_at'):
            excluded_count += 1
            continue

        pr_id = str(pr['number'])
        created_at = pr['created_at']
        merged_at = pr['merged_at']
        labels = [label['name'] for label in pr.get('labels', [])]

        turnaround = calculate_turnaround_hours(created_at, merged_at)
        if turnaround is None:
            excluded_count += 1
            continue

        # Fetch commit messages
        pr_number = int(pr['number'])
        commit_messages = fetch_commits_for_pr(repo_name, pr_number)

        pr_record = {
            "pr_id": pr_id,
            "repo_name": repo_name,
            "created_at": created_at,
            "merged_at": merged_at,
            "turnaround_hours": turnaround,
            "labels": labels,
            "commit_messages": commit_messages
        }

        pr_record['classification'] = classify_pr(pr_record)
        processed.append(pr_record)

    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} PRs from {repo_name} due to missing data.")

    return processed

def fetch_prs_and_commits_for_repos(repos: List[Dict], max_pages: int = 50, timeout_minutes: float = 30.0) -> Tuple[List[Dict], List[str]]:
    """
    Fetch PRs and commits for a list of repositories.
    Stops after max_pages per repo or timeout.
    Returns (all_pr_data, truncated_repos).
    """
    all_pr_data = []
    truncated_repos = []
    start_time = time.time()

    for repo in repos:
        repo_name = repo['name']
        logger.info(f"Processing {repo_name}...")

        page = 1
        prs_for_repo = []
        next_url = None

        while page <= max_pages:
            # Check timeout
            elapsed = (time.time() - start_time) / 60.0
            if elapsed > timeout_minutes:
                logger.warning(f"Timeout reached for {repo_name} after {page} pages. Stopping.")
                truncated_repos.append(repo_name)
                break

            # Fetch PRs
            if next_url:
                # Use the URL from Link header directly
                pr_list, next_url = fetch_prs_for_repo(repo_name, page=1) # API handles page via URL
                # Actually, for the 'next' URL, we should just request that URL
                # Let's adjust: if next_url exists, request next_url, else request page
                pass
            
            # Correct pagination logic using fetch_prs_for_repo
            # We need to handle the 'next' link manually if we want to use the URL directly
            # But fetch_prs_for_repo uses page number. Let's stick to page numbers for simplicity
            # unless the API forces us to use the URL.
            
            pr_list, next_url = fetch_prs_for_repo(repo_name, page=page)
            
            if not pr_list:
                break

            prs_for_repo.extend(pr_list)
            
            if not next_url:
                break
            
            page += 1
            
            # Small delay to be nice to the API
            time.sleep(1)

        # Process collected PRs for this repo
        processed_prs = process_pr_data(repo_name, prs_for_repo)
        all_pr_data.extend(processed_prs)

        # T014 Logic: Check if repo has fewer than MIN_PR_THRESHOLD PRs after filtering
        if len(processed_prs) < MIN_PR_THRESHOLD:
            logger.warning(f"Repository {repo_name} has only {len(processed_prs)} PRs after filtering (threshold: {MIN_PR_THRESHOLD}). Skipping further processing for this repo.")
            # We still saved the PRs to all_pr_data above, but the task says "skip repos".
            # Usually this means exclude from the final dataset.
            # Let's remove them from all_pr_data if we want to strictly "skip".
            # However, the task says "log warnings; explicitly write the list of skipped repository names".
            # It implies we identify them as skipped.
            # Let's remove them from the main dataset to ensure they aren't used in analysis.
            all_pr_data = [p for p in all_pr_data if p['repo_name'] != repo_name]
            
            # Ensure the repo is in the excluded list
            if repo_name not in truncated_repos:
                truncated_repos.append(repo_name)

    return all_pr_data, truncated_repos

def save_excluded_repos(excluded_repos: List[str], output_path: str) -> None:
    """
    Save the list of excluded repository names to a text file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        for repo in excluded_repos:
            f.write(f"{repo}\n")
    logger.info(f"Saved excluded repos to {output_path}")

def save_raw_pr_data(pr_data: List[Dict], output_path: str) -> None:
    """Save raw PR data to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(pr_data, f, indent=2)
    logger.info(f"Saved raw PR data to {output_path}")

def save_processed_data(pr_data: List[Dict], output_path: str) -> None:
    """Save processed PR data to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not pr_data:
        logger.warning("No data to save to processed CSV.")
        # Create empty file with headers? Or just skip.
        # Let's create empty file with headers to avoid downstream errors
        with open(path, 'w') as f:
            f.write("pr_id,repo_name,created_at,merged_at,turnaround_hours,classification,labels,commit_messages\n")
        return

    with open(path, 'w') as f:
        # Write header
        f.write("pr_id,repo_name,created_at,merged_at,turnaround_hours,classification,labels,commit_messages\n")
        for pr in pr_data:
            # Escape commas in commit messages and labels
            labels_str = ";".join(pr.get('labels', []))
            messages_str = ";".join(pr.get('commit_messages', [])).replace('\n', ' ').replace(',', ';')
            row = [
                pr['pr_id'],
                pr['repo_name'],
                pr['created_at'],
                pr['merged_at'],
                str(pr['turnaround_hours']),
                pr['classification'],
                labels_str,
                messages_str
            ]
            f.write(",".join(row) + "\n")
    logger.info(f"Saved processed PR data to {output_path}")

def main():
    """Main entry point for data fetching pipeline."""
    logger.info("Starting data fetching pipeline...")

    # 1. Fetch Repos
    python_repos = fetch_repos_from_github("Python", limit=20)
    js_repos = fetch_repos_from_github("JavaScript", limit=20)
    all_repos = python_repos + js_repos

    if not all_repos:
        logger.error("No repositories fetched. Exiting.")
        return

    logger.info(f"Fetched {len(all_repos)} repositories.")

    # 2. Fetch PRs and Commits
    pr_data, truncated_repos = fetch_prs_and_commits_for_repos(all_repos)

    # 3. Save Excluded Repos (T014)
    # This includes repos that timed out AND repos with < 50 PRs
    save_excluded_repos(truncated_repos, "data/processed/excluded_repos.txt")

    # 4. Save Data
    save_raw_pr_data(pr_data, "data/raw/pr_data.json")
    save_processed_data(pr_data, "data/processed/pr_turnaround.csv")

    logger.info("Data fetching pipeline completed.")

if __name__ == "__main__":
    main()