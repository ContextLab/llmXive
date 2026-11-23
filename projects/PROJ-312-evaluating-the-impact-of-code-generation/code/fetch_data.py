import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import requests

from utils import api_request_with_backoff, log_api_headers, MIN_PR_THRESHOLD, save_excluded_repos

def setup_logging():
    """Configure logging for the fetch_data module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pipeline.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_iso_datetime(iso_string: str) -> datetime:
    """Parse ISO 8601 date string to datetime object."""
    if not iso_string:
        return None
    # Handle 'Z' suffix
    iso_string = iso_string.replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(iso_string)
    except ValueError:
        # Fallback for older Python versions or slight format variations
        return datetime.strptime(iso_string[:19], '%Y-%m-%dT%H:%M:%S')

def extract_commit_keywords(commit_messages: List[str]) -> List[str]:
    """Extract commit messages containing AI-related keywords."""
    keywords = ['copilot', 'ai-generated', 'ai-assisted', 'llm-code']
    return [msg for msg in commit_messages if any(kw in msg.lower() for kw in keywords)]

def check_labels(labels: List[str]) -> bool:
    """Check if any label indicates AI assistance."""
    ai_labels = ['ai-generated', 'copilot-assisted', 'llm-code']
    return any(label.lower() in ai_labels for label in labels)

def classify_pr(commit_messages: List[str], labels: List[str]) -> bool:
    """
    Classify a PR as AI-assisted based on commit messages and labels.
    Returns True if AI-assisted, False otherwise.
    """
    if check_labels(labels):
        return True
    if extract_commit_keywords(commit_messages):
        return True
    return False

def calculate_turnaround_hours(created_at: str, merged_at: str) -> float:
    """Calculate turnaround time in hours between created_at and merged_at."""
    if not created_at or not merged_at:
        return None
    created_dt = parse_iso_datetime(created_at)
    merged_dt = parse_iso_datetime(merged_at)
    if created_dt and merged_dt:
        delta = merged_dt - created_dt
        return delta.total_seconds() / 3600.0
    return None

def fetch_repos_from_github(logger: logging.Logger, language: str = 'Python', min_stars: int = 10000, limit: int = 20) -> List[Dict[str, Any]]:
    """Fetch top repositories for a given language using GitHub API."""
    query = f"language:{language}+stars:>{min_stars}&sort=stars&order=desc"
    url = f"https://api.github.com/search/repositories?q={query}&per_page={limit}"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    
    response = api_request_with_backoff(url, headers, logger)
    log_api_headers(response, logger)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch repos: {response.status_code}")
        return []
    
    data = response.json()
    repos = []
    for item in data.get('items', []):
        repos.append({
            'name': item['full_name'],
            'stars': item['stargazers_count'],
            'language': item['language']
        })
    return repos

def fetch_prs_for_repo(repo_name: str, logger: logging.Logger, page: int = 1) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Fetch PRs for a specific repository page."""
    url = f"https://api.github.com/repos/{repo_name}/pulls"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    params = {'state': 'all', 'per_page': 100, 'page': page}
    
    response = api_request_with_backoff(url, headers, logger)
    log_api_headers(response, logger)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch PRs for {repo_name}: {response.status_code}")
        return [], None
    
    data = response.json()
    # Parse Link header for next page
    link_header = response.headers.get('Link', '')
    next_url = None
    if 'rel="next"' in link_header:
        for part in link_header.split(','):
            if 'rel="next"' in part:
                url_part = part.split(';')[0].strip()
                next_url = url_part[1:-1] # Remove < and >
                break
    
    return data, next_url

def fetch_commits_for_pr(repo_name: str, pr_number: int, logger: logging.Logger) -> List[str]:
    """Fetch commit messages for a specific PR."""
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/commits"
    headers = {'Accept': 'application/vnd.github.v3+json'}
    
    response = api_request_with_backoff(url, headers, logger)
    log_api_headers(response, logger)
    
    if response.status_code != 200:
        logger.warning(f"Failed to fetch commits for PR #{pr_number} in {repo_name}")
        return []
    
    data = response.json()
    return [commit['commit']['message'] for commit in data]

def process_pr_data(repo_name: str, pr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Process a single PR object into our structured format."""
    created_at = pr.get('created_at')
    merged_at = pr.get('merged_at')
    
    # T013: Exclude PRs with missing merged_at
    if not merged_at:
        return None
    
    pr_id = pr.get('number')
    labels = [label['name'] for label in pr.get('labels', [])]
    
    turnaround_hours = calculate_turnaround_hours(created_at, merged_at)
    
    return {
        'pr_id': pr_id,
        'repo_name': repo_name,
        'created_at': created_at,
        'merged_at': merged_at,
        'labels': labels,
        'turnaround_hours': turnaround_hours
    }

def fetch_prs_and_commits_for_repos(repos: List[Dict[str, Any]], logger: logging.Logger, max_pages: int = 50, timeout_seconds: int = 1800) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
    """
    Fetch PRs and commits for a list of repos.
    Returns: (all_pr_data, truncated_repos, excluded_repos)
    """
    all_pr_data = []
    truncated_repos = []
    excluded_repos = []
    start_time = time.time()
    
    for repo in repos:
        repo_name = repo['name']
        logger.info(f"Processing repo: {repo_name}")
        
        page = 1
        prs_fetched = 0
        current_repo_prs = []
        
        while page <= max_pages:
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                logger.warning(f"Timeout reached for {repo_name}. Stopping fetch.")
                truncated_repos.append(repo_name)
                break
            
            prs, next_url = fetch_prs_for_repo(repo_name, logger, page)
            if not prs:
                break
            
            for pr in prs:
                processed = process_pr_data(repo_name, pr)
                if processed:
                    # Fetch commits for classification
                    commit_messages = fetch_commits_for_pr(repo_name, pr['number'], logger)
                    processed['commit_messages'] = commit_messages
                    processed['is_ai_assisted'] = classify_pr(commit_messages, processed['labels'])
                    current_repo_prs.append(processed)
            
            prs_fetched += len(prs)
            
            if next_url:
                page += 1
            else:
                break
        
        # T014: Check repo size threshold
        if len(current_repo_prs) < MIN_PR_THRESHOLD:
            logger.warning(f"Skipping {repo_name}: only {len(current_repo_prs)} PRs found (threshold: {MIN_PR_THRESHOLD})")
            excluded_repos.append(repo_name)
        else:
            all_pr_data.extend(current_repo_prs)
    
    return all_pr_data, truncated_repos, excluded_repos

def save_excluded_repos_to_file(excluded_repos: List[str], output_path: str):
    """Save excluded repos to a file."""
    save_excluded_repos(excluded_repos, output_path)

def save_raw_pr_data(pr_data: List[Dict[str, Any]], output_path: str):
    """Save raw PR data to JSON."""
    with open(output_path, 'w') as f:
        json.dump(pr_data, f, indent=2)

def save_processed_data(pr_data: List[Dict[str, Any]], output_path: str):
    """Save processed PR data to CSV."""
    import csv
    if not pr_data:
        return
    
    keys = pr_data[0].keys()
    with open(output_path, 'w', newline='') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(pr_data)

def main():
    """Main entry point for data fetching."""
    logger = setup_logging()
    
    # Fetch repos
    python_repos = fetch_repos_from_github(logger, 'Python')
    js_repos = fetch_repos_from_github(logger, 'JavaScript')
    all_repos = python_repos + js_repos
    
    logger.info(f"Fetched {len(all_repos)} repositories")
    
    # Fetch PRs and commits
    pr_data, truncated_repos, excluded_repos = fetch_prs_and_commits_for_repos(all_repos, logger)
    
    # Save outputs
    os.makedirs('data/raw', exist_ok=True)
    os.makedirs('data/processed', exist_ok=True)
    
    save_raw_pr_data(pr_data, 'data/raw/pr_data.json')
    save_processed_data(pr_data, 'data/processed/pr_turnaround.csv')
    
    # Save excluded repos (T014)
    if excluded_repos:
        save_excluded_repos_to_file(excluded_repos, 'data/processed/excluded_repos.txt')
        logger.info(f"Saved {len(excluded_repos)} excluded repos to data/processed/excluded_repos.txt")
    
    # Save truncated repos if any
    if truncated_repos:
        with open('data/processed/truncated_repos.txt', 'w') as f:
            for repo in truncated_repos:
                f.write(f"{repo}\n")
        logger.info(f"Saved {len(truncated_repos)} truncated repos")

if __name__ == '__main__':
    main()
