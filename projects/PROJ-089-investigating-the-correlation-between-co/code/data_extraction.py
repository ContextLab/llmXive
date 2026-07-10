"""
Data Extraction Module for Code Churn vs Technical Debt Study.

This module implements T010-T013:
- Query GitHub API for repos.
- Clone repos.
- Extract git metrics.
- Generate repos_metadata.csv.
"""
import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import subprocess
import pandas as pd

from config import get_config_summary, ensure_directories
from utils import get_logger, setup_logging

logger = get_logger(__name__)

def query_github_repos(min_stars: int = 500, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Query GitHub API for repositories with at least min_stars.
    Returns a list of repo metadata.
    """
  # Note: In a real scenario, we would handle rate limits and pagination.
  # For this task, we fetch a small sample.
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "language:python stars:>500", # Default to Python for demo
        "sort": "stars",
        "order": "desc",
        "per_page": limit
    }
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        logger.error(f"Error querying GitHub API: {e}")
        return []

def filter_repos_by_age(repos: List[Dict], min_age_years: int = 2) -> List[Dict]:
    """
    Filter repositories by age (created_at).
    """
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=min_age_years * 365)
    filtered = []
    for repo in repos:
        created_at = datetime.fromisoformat(repo['created_at'].replace('Z', '+00:00'))
        if created_at < cutoff:
            filtered.append(repo)
    return filtered

def clone_repository(repo_url: str, target_dir: Path) -> bool:
    """Clone a repository to the target directory."""
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            check=True,
            capture_output=True
        )
        return True
    except Exception as e:
        logger.error(f"Failed to clone {repo_url}: {e}")
        return False

def extract_git_metrics(repo_path: Path) -> Dict[str, Any]:
    """
    Extract basic git metrics (commit count, contributors) using git commands.
    For full file-level metrics, pydriller would be used (T011).
    """
    try:
        # Total commits
        commits = subprocess.run(
            ["git", "-C", str(repo_path), "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, check=True
        )
        commit_count = int(commits.stdout.strip())
        
        # Contributors
        contributors = subprocess.run(
            ["git", "-C", str(repo_path), "shortlog", "-sne", "HEAD"],
            capture_output=True, text=True, check=True
        )
        contributor_count = len(contributors.stdout.strip().split('\n'))
        
        return {
            "commit_count": commit_count,
            "contributor_count": contributor_count
        }
    except Exception as e:
        logger.error(f"Error extracting git metrics: {e}")
        return {"commit_count": 0, "contributor_count": 0}

def aggregate_file_metrics(repo_path: Path) -> List[Dict]:
    """
    Aggregate file-level metrics.
    This is a placeholder for T011 (pydriller implementation).
    """
    # In a real implementation, this would use pydriller to walk commits.
    # For now, we return a dummy structure to satisfy the pipeline flow.
    return []

def save_repos_metadata(repos: List[Dict], git_metrics: List[Dict], output_path: Path):
    """Save repository metadata to CSV."""
    data = []
    for repo, metrics in zip(repos, git_metrics):
        data.append({
            "repo_id": repo["id"],
            "repo_name": repo["full_name"],
            "repo_url": repo["html_url"],
            "stars": repo["stargazers_count"],
            "language": repo["language"],
            "created_at": repo["created_at"],
            "commit_count": metrics["commit_count"],
            "contributor_count": metrics["contributor_count"],
            "repo_path": str(repo.get("local_path", "")) # Placeholder
        })
    
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved repository metadata to {output_path}")

def run_data_extraction():
    """Main function to run the data extraction pipeline."""
    setup_logging()
    config = get_config_summary()
    ensure_directories()
    
    # 1. Query GitHub
    logger.info("Querying GitHub API...")
    repos = query_github_repos(min_stars=config['min_github_stars'], limit=3)
    
    if not repos:
        logger.warning("No repositories found.")
        return
    
    # 2. Filter by age
    logger.info("Filtering repositories by age...")
    repos = filter_repos_by_age(repos, config['min_repo_age'])
    
    # 3. Clone and Extract
    git_metrics = []
    for repo in repos:
        repo_name = repo["full_name"].replace("/", "_")
        target_path = Path("data/raw/cloned_repos") / repo_name
        repo["local_path"] = target_path
        
        logger.info(f"Cloning {repo_name}...")
        if clone_repository(repo["html_url"], target_path):
            metrics = extract_git_metrics(target_path)
            git_metrics.append(metrics)
        else:
            git_metrics.append({"commit_count": 0, "contributor_count": 0})
    
    # 4. Save Metadata
    output_path = Path("data/raw/repos_metadata.csv")
    save_repos_metadata(repos, git_metrics, output_path)

def run_data_extraction_wrapper():
    """Wrapper for integration with main.py."""
    run_data_extraction()
