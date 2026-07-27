import os
import json
import csv
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import get_config
from utils.github_client import GitHubClient
from utils.metrics import (
    calculate_iteration_count,
    calculate_avg_comment_length,
    calculate_review_thread_depth,
    calculate_revert_frequency,
    calculate_diff_complexity_score,
    is_ai_noise_flag,
    calculate_domain_complexity,
    process_review_metrics
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_repo_list(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Load the list of repositories to analyze from a configuration file or list."""
    repo_list_path = config.get('repo_list_path', 'data/raw/repo_list.json')
    if os.path.exists(repo_list_path):
        with open(repo_list_path, 'r') as f:
            return json.load(f)
    else:
        # Fallback to a default list if file not found (for testing purposes)
        logger.warning(f"Repo list file not found at {repo_list_path}. Using default list.")
        return [
            {"owner": "microsoft", "name": "vscode"},
            {"owner": "facebook", "name": "react"},
            {"owner": "pytorch", "name": "pytorch"}
        ]

def fetch_repository_details(client: GitHubClient, repo_list: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fetch detailed metadata for each repository in the list."""
    results = []
    for repo in repo_list:
        owner = repo.get('owner')
        name = repo.get('name')
        if not owner or not name:
            logger.warning(f"Skipping invalid repo entry: {repo}")
            continue

        try:
            details = client.get_repo_details(owner, name)
            if details:
                details['owner'] = owner
                details['name'] = name
                results.append(details)
            else:
                logger.warning(f"Failed to fetch details for {owner}/{name}")
        except Exception as e:
            logger.error(f"Error fetching details for {owner}/{name}: {e}")
    return results

def calculate_llm_adoption_flag(repo_details: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """
    Determine if a repository is using LLM-based code completion.
    Checks for:
    - .cursorrules or copilot config files
    - README.md/CONTRIBUTING.md mentions of "Copilot"/"LLM"
    - Commit message frequency >= 5% containing "Copilot"/"LLM"
    """
    # Check for config files
    config_files = repo_details.get('config_files', [])
    has_cursorrules = any('.cursorrules' in f for f in config_files)
    has_copilot_config = any('copilot' in f.lower() for f in config_files)
    
    if has_cursorrules or has_copilot_config:
        return True

    # Check README/CONTRIBUTING content
    readme_content = repo_details.get('readme_content', '').lower()
    contributing_content = repo_details.get('contributing_content', '').lower()
    if 'copilot' in readme_content or 'llm' in readme_content:
        return True
    if 'copilot' in contributing_content or 'llm' in contributing_content:
        return True

    # Check commit message frequency
    commits = repo_details.get('commits', [])
    if not commits:
        return False
    
    copilot_count = sum(1 for c in commits if 'copilot' in c.get('message', '').lower() or 'llm' in c.get('message', '').lower())
    frequency = copilot_count / len(commits)
    
    return frequency >= 0.05

def filter_min_pull_requests(repo_details: List[Dict[str, Any]], min_prs: int = 10, window_months: int = 12) -> List[Dict[str, Any]]:
    """
    Filter repositories to include only those with at least `min_prs` pull requests
    in the last `window_months` months.
    
    This implements SC-001: "The analysis must exclude repositories with fewer
    than 10 pull requests in the past 12 months."
    """
    import datetime
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=window_months * 30)
    filtered = []
    
    for repo in repo_details:
        prs = repo.get('pull_requests', [])
        recent_prs = [
            pr for pr in prs
            if pr.get('created_at') and datetime.datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00')) > cutoff_date
        ]
        
        if len(recent_prs) >= min_prs:
            repo['recent_pr_count'] = len(recent_prs)
            filtered.append(repo)
        else:
            logger.info(f"Filtering out {repo.get('owner')}/{repo.get('name')}: only {len(recent_prs)} PRs in last {window_months} months (threshold: {min_prs})")
    
    return filtered

def run_ingestion(config_path: str = 'config.yaml') -> None:
    """Main ingestion pipeline: load repos, fetch details, filter, calculate metrics, write CSV."""
    config = get_config(config_path)
    
    # Load repo list
    repo_list = load_repo_list(config)
    logger.info(f"Loaded {len(repo_list)} repositories from list")
    
    # Initialize GitHub client
    client = GitHubClient(token=config.get('github_token'))
    
    # Fetch details
    repo_details = fetch_repository_details(client, repo_list, config)
    logger.info(f"Fetched details for {len(repo_details)} repositories")
    
    # Apply SC-001 filter: minimum pull requests
    filtered_repos = filter_min_pull_requests(repo_details, min_prs=10, window_months=12)
    logger.info(f"After filtering for min PRs: {len(filtered_repos)} repositories")
    
    # Calculate metrics and prepare output
    output_rows = []
    for repo in filtered_repos:
        llm_flag = calculate_llm_adoption_flag(repo, config)
        
        # Calculate metrics
        iterations = calculate_iteration_count(repo.get('pull_requests', []))
        avg_comment = calculate_avg_comment_length(repo.get('pull_requests', []))
        review_depth = calculate_review_thread_depth(repo.get('pull_requests', []))
        revert_freq = calculate_revert_frequency(repo.get('commits', []))
        domain_complexity = calculate_domain_complexity(repo.get('languages', []), repo.get('dependencies', []))
        
        # Process review metrics
        processed_metrics = process_review_metrics(repo.get('pull_requests', []))
        
        row = {
            'owner': repo.get('owner'),
            'name': repo.get('name'),
            'llm_adoption_flag': llm_flag,
            'iteration_count': iterations,
            'avg_comment_length': avg_comment,
            'review_thread_depth': review_depth,
            'revert_frequency': revert_freq,
            'domain_complexity': domain_complexity,
            'recent_pr_count': repo.get('recent_pr_count', 0),
            **processed_metrics
        }
        output_rows.append(row)
    
    # Write output
    output_path = config.get('output_path', 'data/derived/master_dataset.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=output_rows[0].keys() if output_rows else [])
        writer.writeheader()
        writer.writerows(output_rows)
    
    logger.info(f"Wrote {len(output_rows)} rows to {output_path}")

if __name__ == '__main__':
    run_ingestion()
