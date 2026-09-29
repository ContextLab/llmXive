import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

from utils import api_request_with_backoff, log_api_headers, MIN_PR_THRESHOLD

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_iso_datetime(iso_str: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string."""
    if not iso_str:
        return None
    try:
        # Handle 'Z' suffix and varying formats
        iso_str = iso_str.replace('Z', '+00:00')
        if '+' not in iso_str and '-' not in iso_str[10:]:
            iso_str += '+00:00'
        return datetime.fromisoformat(iso_str)
    except ValueError as e:
        logger.warning(f"Failed to parse date {iso_str}: {e}")
        return None

def extract_commit_keywords(message: str) -> List[str]:
    """Extract AI-related keywords from commit message."""
    if not message:
        return []
    message_lower = message.lower()
    keywords = []
    if 'copilot' in message_lower:
        keywords.append('copilot')
    if 'ai-generated' in message_lower:
        keywords.append('ai-generated')
    if 'ai-assisted' in message_lower:
        keywords.append('ai-assisted')
    if 'llm' in message_lower:
        keywords.append('llm')
    return keywords

def check_labels(labels: List[Dict[str, Any]], ai_keywords: List[str]) -> bool:
    """Check if PR has AI-related labels."""
    ai_label_names = {'ai-generated', 'copilot-assisted', 'llm-code', 'ai-assisted'}
    for label in labels:
        label_name = label.get('name', '').lower()
        if label_name in ai_label_names:
            return True
    return False

def classify_pr(pr_data: Dict[str, Any]) -> bool:
    """
    Classify PR as AI-assisted based on commit messages and labels.
    Returns True if AI-assisted, False otherwise.
    """
    # Check labels first
    labels = pr_data.get('labels', [])
    if check_labels(labels, []):
        return True

    # Check commit messages
    commits = pr_data.get('commits', [])
    for commit in commits:
        message = commit.get('message', '')
        if extract_commit_keywords(message):
            return True

    return False

def calculate_turnaround_hours(created_at: str, merged_at: str) -> Optional[float]:
    """Calculate turnaround time in hours."""
    created = parse_iso_datetime(created_at)
    merged = parse_iso_datetime(merged_at)
    
    if not created or not merged:
        return None
    
    delta = merged - created
    return delta.total_seconds() / 3600.0

def fetch_repos_from_github(token: Optional[str] = None, top_n: int = 20) -> List[Dict[str, Any]]:
    """Fetch top repositories for Python and JavaScript."""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    repos = []
    languages = ['Python', 'JavaScript']
    
    for lang in languages:
        query = f"language:{lang}+stars:>10000"
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=100"
        
        page = 1
        while page <= 2 and len(repos) < top_n:  # Fetch up to 2 pages
            try:
                response = api_request_with_backoff(url, headers)
                log_api_headers(response)
                
                if response.status_code != 200:
                    logger.error(f"Failed to fetch repos for {lang}: {response.status_code}")
                    break
                
                data = response.json()
                items = data.get('items', [])
                
                for item in items:
                    if len(repos) >= top_n:
                        break
                    repos.append({
                        'name': item['full_name'],
                        'stars': item['stargazers_count'],
                        'language': item['language']
                    })
                
                # Check for next page
                if 'next' not in response.links:
                    break
                url = response.links['next']['url']
                page += 1
                
            except Exception as e:
                logger.error(f"Error fetching repos: {e}")
                break
    
    return repos[:top_n]

def fetch_prs_for_repo(repo_name: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all PRs for a repository with pagination."""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    prs = []
    url = f"https://api.github.com/repos/{repo_name}/pulls?state=all&per_page=100"
    page = 1
    
    while True:
        try:
            response = api_request_with_backoff(url, headers)
            log_api_headers(response)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch PRs for {repo_name}: {response.status_code}")
                break
            
            data = response.json()
            if not data:
                break
            
            prs.extend(data)
            
            # Check for next page
            if 'next' not in response.links:
                break
            url = response.links['next']['url']
            page += 1
            
            # Safety stop condition
            if page > 50:
                logger.warning(f"Reached max pages (50) for {repo_name}")
                break
            
            time.sleep(1)  # Rate limiting safety
            
        except Exception as e:
            logger.error(f"Error fetching PRs for {repo_name}: {e}")
            break
    
    return prs

def fetch_commits_for_pr(repo_name: str, pr_number: int, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch commits for a specific PR."""
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/commits?per_page=100"
    commits = []
    
    try:
        response = api_request_with_backoff(url, headers)
        log_api_headers(response)
        
        if response.status_code == 200:
            commits = response.json()
        else:
            logger.warning(f"Failed to fetch commits for PR #{pr_number}: {response.status_code}")
            
    except Exception as e:
        logger.error(f"Error fetching commits for PR #{pr_number}: {e}")
    
    return commits

def process_pr_data(repo_name: str, pr_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process PR data: filter, classify, calculate turnaround."""
    processed_prs = []
    excluded_count = 0
    
    for pr in pr_list:
        # Skip unmerged PRs
        if not pr.get('merged_at'):
            excluded_count += 1
            continue
        
        pr_number = pr.get('number')
        created_at = pr.get('created_at')
        merged_at = pr.get('merged_at')
        
        # Fetch commits
        commits = fetch_commits_for_pr(repo_name, pr_number)
        
        # Calculate turnaround
        turnaround = calculate_turnaround_hours(created_at, merged_at)
        if turnaround is None:
            excluded_count += 1
            continue
        
        # Build PR data object
        pr_data = {
            'pr_id': f"{repo_name}#{pr_number}",
            'repo_name': repo_name,
            'created_at': created_at,
            'merged_at': merged_at,
            'turnaround_hours': turnaround,
            'labels': pr.get('labels', []),
            'commits': commits,
            'is_ai_assisted': classify_pr(pr)
        }
        
        processed_prs.append(pr_data)
    
    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} PRs from {repo_name} due to missing data")
    
    return processed_prs

def fetch_prs_and_commits_for_repos(repos: List[Dict[str, Any]], token: Optional[str] = None) -> tuple:
    """
    Fetch PRs and commits for all repositories.
    Returns (all_prs, excluded_repos) where excluded_repos are those with < MIN_PR_THRESHOLD PRs.
    """
    all_prs = []
    excluded_repos = []
    
    for repo_info in repos:
        repo_name = repo_info['name']
        logger.info(f"Fetching PRs for {repo_name}...")
        
        pr_list = fetch_prs_for_repo(repo_name, token)
        
        # Filter PRs with merged_at and calculate turnaround
        processed = process_pr_data(repo_name, pr_list)
        
        # Check threshold
        if len(processed) < MIN_PR_THRESHOLD:
            logger.warning(f"Repository {repo_name} has only {len(processed)} PRs (< {MIN_PR_THRESHOLD}), skipping.")
            excluded_repos.append(repo_name)
        else:
            all_prs.extend(processed)
            logger.info(f"Added {len(processed)} PRs from {repo_name}")
    
    return all_prs, excluded_repos

def save_excluded_repos(excluded_repos: List[str], output_path: str) -> None:
    """Save list of excluded repository names to a file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        for repo in excluded_repos:
            f.write(f"{repo}\n")
    
    logger.info(f"Saved {len(excluded_repos)} excluded repositories to {output_path}")

def main():
    """Main entry point for data fetching pipeline."""
    token = os.getenv('GITHUB_TOKEN')
    
    # Fetch repos
    repos = fetch_repos_from_github(token)
    logger.info(f"Fetched {len(repos)} repositories")
    
    # Fetch PRs and classify
    all_prs, excluded_repos = fetch_prs_and_commits_for_repos(repos, token)
    
    # Save excluded repos
    excluded_file = "data/processed/excluded_repos.txt"
    save_excluded_repos(excluded_repos, excluded_file)
    
    # Save raw data
    raw_data_path = "data/raw/pr_data.json"
    Path(raw_data_path).parent.mkdir(parents=True, exist_ok=True)
    with open(raw_data_path, 'w') as f:
        json.dump(all_prs, f, indent=2)
    
    logger.info(f"Pipeline complete. Total PRs: {len(all_prs)}, Excluded repos: {len(excluded_repos)}")
    return all_prs, excluded_repos

if __name__ == "__main__":
    main()