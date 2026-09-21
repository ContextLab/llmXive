"""
Data fetching module for GitHub API interactions.

This module handles fetching repositories, PRs, and commits,
and processing them for turnaround time analysis.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

from utils import api_request_with_backoff, validate_json_schema, log_api_headers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"

def extract_commit_keywords(message: str) -> List[str]:
    """
    Extract AI-related keywords from a commit message.
    
    Args:
        message: The commit message string
    
    Returns:
        List of matched keywords
    """
    if not message:
        return []
    
    message_lower = message.lower()
    keywords = ['copilot', 'ai-generated', 'ai-assisted', 'llm-code', 'github copilot']
    found = [kw for kw in keywords if kw in message_lower]
    return list(set(found))

def check_labels(pr_data: Dict[str, Any], ai_labels: List[str] = None) -> bool:
    """
    Check if a PR has any AI-related labels.
    
    Args:
        pr_data: PR data dictionary
        ai_labels: List of AI-related label names
    
    Returns:
        True if any AI label is present
    """
    if ai_labels is None:
        ai_labels = ['ai-generated', 'copilot-assisted', 'llm-code']
    
    labels = pr_data.get('labels', [])
    label_names = [label.get('name', '').lower() for label in labels]
    
    return any(label in ai_labels for label in label_names)

def classify_pr(pr_data: Dict[str, Any]) -> str:
    """
    Classify a PR as 'AI-assisted' or 'Non-AI' based on commits and labels.
    
    Args:
        pr_data: PR data dictionary including commits and labels
    
    Returns:
        Classification string
    """
    # Check labels first
    if check_labels(pr_data):
        return 'AI-assisted'
    
    # Check commit messages
    commits = pr_data.get('commits', [])
    for commit in commits:
        message = commit.get('message', '')
        if extract_commit_keywords(message):
            return 'AI-assisted'
    
    return 'Non-AI'

def fetch_repos_from_github(language: str, min_stars: int = 10000, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch top repositories by language and star count.
    
    Args:
        language: Programming language (e.g., 'Python', 'JavaScript')
        min_stars: Minimum star count filter
        limit: Maximum number of repos to return
    
    Returns:
        List of repository dictionaries
    """
    query = f"language:{language}+stars:>{min_stars}&sort=stars&order=desc"
    url = f"{GITHUB_API_BASE}/search/repositories?q={query}"
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'llmXive-Pipeline'
    }
    
    response = api_request_with_backoff(url, headers)
    if not response or response.status_code != 200:
        logger.error(f"Failed to fetch repos for {language}: {response.status_code if response else 'No response'}")
        return []
    
    data = response.json()
    items = data.get('items', [])[:limit]
    
    # Format output
    repos = []
    for item in items:
        repos.append({
            'name': item['full_name'],
            'stars': item['stargazers_count'],
            'url': item['html_url']
        })
    
    logger.info(f"Fetched {len(repos)} {language} repositories")
    return repos

def fetch_prs_for_repo(repo_name: str) -> List[Dict[str, Any]]:
    """
    Fetch all merged PRs for a given repository.
    
    Args:
        repo_name: Full repo name (owner/repo)
    
    Returns:
        List of PR dictionaries
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/pulls?state=closed&per_page=100"
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'llmXive-Pipeline'
    }
    
    all_prs = []
    page = 1
    
    while True:
        response = api_request_with_backoff(url + f"&page={page}", headers)
        if not response or response.status_code != 200:
            break
        
        prs = response.json()
        if not prs:
            break
        
        # Only include merged PRs
        merged_prs = [p for p in prs if p.get('merged_at') is not None]
        all_prs.extend(merged_prs)
        
        if len(prs) < 100:
            break
        
        page += 1
        time.sleep(1)  # Be nice to the API
    
    logger.info(f"Fetched {len(all_prs)} merged PRs for {repo_name}")
    return all_prs

def fetch_commits_for_pr(repo_name: str, pr_number: int) -> List[Dict[str, Any]]:
    """
    Fetch all commits for a specific PR.
    
    Args:
        repo_name: Full repo name
        pr_number: PR number
    
    Returns:
        List of commit dictionaries
    """
    url = f"{GITHUB_API_BASE}/repos/{repo_name}/pulls/{pr_number}/commits?per_page=100"
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'llmXive-Pipeline'
    }
    
    all_commits = []
    page = 1
    
    while True:
        response = api_request_with_backoff(url + f"&page={page}", headers)
        if not response or response.status_code != 200:
            break
        
        commits = response.json()
        if not commits:
            break
        
        all_commits.extend(commits)
        
        if len(commits) < 100:
            break
        
        page += 1
        time.sleep(1)
    
    return all_commits

def parse_iso_datetime(iso_string: str) -> Optional[datetime]:
    """
    Parse ISO 8601 datetime string.
    
    Args:
        iso_string: ISO formatted datetime string
    
    Returns:
        datetime object or None
    """
    if not iso_string:
        return None
    
    try:
        # Handle 'Z' suffix
        iso_string = iso_string.replace('Z', '+00:00')
        return datetime.fromisoformat(iso_string)
    except ValueError:
        logger.warning(f"Failed to parse datetime: {iso_string}")
        return None

def calculate_turnaround_hours(created_at: str, merged_at: str) -> Optional[float]:
    """
    Calculate turnaround time in hours.
    
    Args:
        created_at: PR creation timestamp
        merged_at: PR merge timestamp
    
    Returns:
        Turnaround time in hours, or None if invalid
    """
    created = parse_iso_datetime(created_at)
    merged = parse_iso_datetime(merged_at)
    
    if created and merged:
        delta = merged - created
        return delta.total_seconds() / 3600.0
    
    return None

def process_pr_data(repo_name: str, pr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single PR into the standardized format.
    
    Args:
        repo_name: Repository name
        pr: PR data dictionary
    
    Returns:
        Processed PR dictionary or None
    """
    # Skip if not merged
    if not pr.get('merged_at'):
        return None
    
    pr_id = str(pr['number'])
    created_at = pr.get('created_at')
    merged_at = pr.get('merged_at')
    
    turnaround = calculate_turnaround_hours(created_at, merged_at)
    if turnaround is None:
        return None
    
    # Fetch commits
    commits_raw = fetch_commits_for_pr(repo_name, int(pr_id))
    commits = []
    for c in commits_raw:
        commits.append({
            'sha': c.get('sha'),
            'message': c.get('commit', {}).get('message', ''),
            'author': c.get('commit', {}).get('author', {}).get('name', '')
        })
    
    # Classification
    classification = classify_pr({
        'labels': pr.get('labels', []),
        'commits': commits
    })
    
    return {
        'pr_id': pr_id,
        'repo_name': repo_name,
        'created_at': created_at,
        'merged_at': merged_at,
        'turnaround_hours': turnaround,
        'classification': classification,
        'commits': commits,
        'labels': [l.get('name') for l in pr.get('labels', [])]
    }

def main():
    """Main entry point for data fetching."""
    logger.info("Starting data fetching pipeline")
    
    # Example: Fetch repos (would be parameterized in real run)
    # repos = fetch_repos_from_github("Python")
    # for repo in repos:
    #     prs = fetch_prs_for_repo(repo['name'])
    #     for pr in prs:
    #         data = process_pr_data(repo['name'], pr)
    #         if data:
    #             logger.info(f"Processed PR {data['pr_id']}")
    
    logger.info("Data fetching pipeline complete")

if __name__ == "__main__":
    main()