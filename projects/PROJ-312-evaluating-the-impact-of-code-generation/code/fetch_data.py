import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from existing API surface
from utils import api_request_with_backoff, log_api_headers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def extract_commit_keywords(commit_message: str) -> List[str]:
    """Extract AI-related keywords from commit message."""
    if not commit_message:
        return []
    message_lower = commit_message.lower()
    keywords = ["copilot", "ai-generated", "ai-generated-code", "llm", "gpt"]
    return [kw for kw in keywords if kw in message_lower]

def check_labels(labels: List[str]) -> List[str]:
    """Check for AI-related labels."""
    ai_labels = ["ai-generated", "copilot-assisted", "llm-code"]
    return [label for label in labels if label in ai_labels]

def classify_pr(commit_messages: List[str], labels: List[str]) -> str:
    """
    Classify a PR as 'AI-assisted' or 'non-AI-labeled'.
    Returns 'AI-assisted' if any commit message contains keywords OR labels match.
    """
    for msg in commit_messages:
        if extract_commit_keywords(msg):
            return "AI-assisted"
    
    if check_labels(labels):
        return "AI-assisted"
    
    return "non-AI-labeled"

def fetch_repos_from_github() -> List[Dict[str, Any]]:
    """
    Fetch top repositories from GitHub API.
    Returns a list of repo objects with 'name' and 'stars'.
    """
    repos = []
    # Python repos
    url_py = "https://api.github.com/search/repositories?q=language:Python+stars:>10000&sort=stars&order=desc"
    # JS repos
    url_js = "https://api.github.com/search/repositories?q=language:JavaScript+stars:>10000&sort=stars&order=desc"
    
    for url in [url_py, url_js]:
        response = api_request_with_backoff(url, headers={})
        log_api_headers(response)
        if response.status_code == 200:
            items = response.json().get('items', [])
            repos.extend([{'name': item['name'], 'stars': item['stargazers_count']} for item in items])
        else:
            logger.error(f"Failed to fetch repos from {url}: {response.status_code}")
    return repos

def fetch_prs_for_repo(repo_name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch PRs for a specific repository.
    Handles pagination via Link header.
    """
    prs = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo_name}/pulls?state=closed&per_page=100&page={page}"
        response = api_request_with_backoff(url, headers={})
        log_api_headers(response)
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch PRs for {repo_name} (page {page}): {response.status_code}")
            break
        
        items = response.json()
        if not items:
            break
        
        prs.extend(items)
        if len(prs) >= limit:
            break
        
        # Check for next page
        link_header = response.headers.get('Link', '')
        if 'rel="next"' not in link_header:
            break
        page += 1
        
        # Rate limit safety
        time.sleep(1)
    
    return prs[:limit]

def fetch_commits_for_pr(repo_name: str, pr_number: int) -> List[str]:
    """Fetch commit messages for a specific PR."""
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/commits"
    response = api_request_with_backoff(url, headers={})
    log_api_headers(response)
    
    if response.status_code != 200:
        return []
    
    commits = response.json()
    return [c.get('commit', {}).get('message', '') for c in commits if c.get('commit')]

def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None

def calculate_turnaround_hours(created_at: str, merged_at: str) -> Optional[float]:
    """Calculate turnaround time in hours."""
    created = parse_iso_datetime(created_at)
    merged = parse_iso_datetime(merged_at)
    
    if created and merged:
        delta = merged - created
        return delta.total_seconds() / 3600.0
    return None

def process_pr_data(repos: List[Dict[str, Any]], max_prs_per_repo: int = 50) -> List[Dict[str, Any]]:
    """
    Main data processing loop:
    1. Fetch PRs for each repo
    2. Filter out PRs without merged_at
    3. Fetch commits for classification
    4. Calculate turnaround time
    5. Return list of processed PR records
    """
    all_pr_data = []
    
    for repo in repos:
        repo_name = repo['name']
        logger.info(f"Processing repository: {repo_name}")
        
        prs = fetch_prs_for_repo(repo_name, limit=max_prs_per_repo)
        
        for pr in prs:
            # T013: Exclude PRs with missing merged_at
            if not pr.get('merged_at'):
                continue
            
            pr_id = str(pr['number'])
            created_at = pr.get('created_at', '')
            merged_at = pr.get('merged_at', '')
            
            turnaround = calculate_turnaround_hours(created_at, merged_at)
            if turnaround is None:
                continue
            
            # Fetch commits for classification
            commit_messages = fetch_commits_for_pr(repo_name, pr['number'])
            labels = [l['name'] for l in pr.get('labels', [])]
            
            classification = classify_pr(commit_messages, labels)
            
            record = {
                'pr_id': pr_id,
                'repo_name': repo_name,
                'created_at': created_at,
                'merged_at': merged_at,
                'turnaround_hours': turnaround,
                'classification': classification,
                'commit_messages': commit_messages,
                'labels': labels
            }
            all_pr_data.append(record)
    
    return all_pr_data

def main():
    """
    Main entry point for data fetching.
    Executes the full pipeline and saves intermediate raw data.
    """
    logger.info("Starting data fetching pipeline (T012a, T012b, T013, T015, T016)")
    
    # T012a: Fetch repos
    repos = fetch_repos_from_github()
    logger.info(f"Fetched {len(repos)} repositories")
    
    if not repos:
        logger.error("No repositories fetched. Aborting.")
        return

    # T012b, T013, T015, T016: Process PRs
    pr_data = process_pr_data(repos, max_prs_per_repo=50)
    logger.info(f"Processed {len(pr_data)} PRs")
    
    # Save intermediate raw data for T018a
    output_path = Path("data/raw/pr_data_raw_temp.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(pr_data, f, indent=2, default=str)
    
    logger.info(f"Intermediate raw data saved to {output_path}. Run save_raw_data.py to finalize T018a.")

if __name__ == "__main__":
    main()
