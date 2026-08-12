import os
import time
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import requests
import json
from datetime import datetime, timedelta
import pydriller

from config import get_config_summary, ensure_directories, get_env_override
from utils import get_logger, pin_random_seed

logger = get_logger(__name__)

def query_github_repos(min_stars: int = 500, min_age_days: int = 730, language: str = "Python") -> List[Dict[str, Any]]:
    """
    Query GitHub API for repositories matching criteria.
    Returns a list of repo metadata dictionaries.
    """
    config = get_config_summary()
    token = get_env_override("GITHUB_TOKEN", "")
    headers = {"Authorization": f"token {token}"} if token else {}
    
    # Construct search query
    query = f"language:{language} stars:>{min_stars} pushed:<{datetime.now() - timedelta(days=min_age_days)}"
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 100}
    
    repos = []
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        for item in data.get("items", []):
            repos.append({
                "repo_id": item["id"],
                "full_name": item["full_name"],
                "name": item["name"],
                "stargazers_count": item["stargazers_count"],
                "language": item.get("language"),
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
                "description": item.get("description", ""),
                "clone_url": item["clone_url"],
                "default_branch": item["default_branch"]
            })
        logger.info(f"Found {len(repos)} repositories matching criteria.")
    except Exception as e:
        logger.error(f"Failed to query GitHub API: {e}")
        raise
    return repos

def clone_repository(repo_url: str, dest_path: Path, branch: str = "main") -> bool:
    """
    Clone a repository to dest_path. Returns True on success.
    """
    if dest_path.exists():
        shutil.rmtree(dest_path)
    dest_path.mkdir(parents=True, exist_ok=True)
    try:
        # Use git clone via subprocess or pydriller
        from git import Repo
        Repo.clone_from(repo_url, str(dest_path), branch=branch)
        logger.info(f"Cloned {repo_url} to {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to clone {repo_url}: {e}")
        return False

def extract_git_metrics(repo_path: Path, lookback_days: int = 730) -> List[Dict[str, Any]]:
    """
    Extract per-file commit counts and lines changed in the last N days using pydriller.
    Returns a list of file-level metrics.
    """
    cutoff_date = datetime.now() - timedelta(days=lookback_days)
    file_metrics: Dict[str, Dict[str, Any]] = {}
    
    try:
        repo = pydriller.Repository(str(repo_path))
        for commit in repo.get_commits_from(cutoff_date):
            for modified_file in commit.modified_files:
                path = modified_file.filename
                if not path:
                    continue
                if path not in file_metrics:
                    file_metrics[path] = {"path": path, "commits": 0, "lines_added": 0, "lines_deleted": 0}
                file_metrics[path]["commits"] += 1
                file_metrics[path]["lines_added"] += modified_file.added
                file_metrics[path]["lines_deleted"] += modified_file.removed
    except Exception as e:
        logger.error(f"Error extracting git metrics from {repo_path}: {e}")
        return []
    
    return list(file_metrics.values())

def aggregate_file_metrics(file_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate file metrics into summary stats (total lines changed, avg loc, etc).
    """
    if not file_metrics:
        return {"total_lines_changed": 0, "avg_loc": 0.0, "contributor_count": 0}
    
    total_changed = sum(m["lines_added"] + m["lines_deleted"] for m in file_metrics)
    # Note: avg_loc is a covariate, but here we just compute a placeholder or placeholder logic
    # In a real pipeline, avg_loc would come from static analysis (T014) or file size.
    # For T012, we just ensure the structure exists; actual values come from T014/T015.
    return {
        "total_lines_changed": total_changed,
        "avg_loc": 0.0,  # Placeholder, to be filled by static analysis
        "contributor_count": len(set(m.get("path", "") for m in file_metrics))
    }

def save_repos_metadata(repos: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save repository metadata to a CSV file.
    """
    if not repos:
        logger.warning("No repositories to save.")
        return
    
    df = pd.DataFrame(repos)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def process_single_repo(repo: Dict[str, Any], work_dir: Path, lookback_days: int = 730) -> Optional[Dict[str, Any]]:
    """
    Process a single repository: clone, extract metrics, and return metadata.
    """
    repo_name = repo["full_name"].replace("/", "_")
    repo_path = work_dir / repo_name
    
    if not clone_repository(repo["clone_url"], repo_path):
        return None
    
    file_metrics = extract_git_metrics(repo_path, lookback_days)
    if not file_metrics:
        shutil.rmtree(repo_path)
        return None
    
    aggregated = aggregate_file_metrics(file_metrics)
    result = {
        "repo_id": repo["repo_id"],
        "full_name": repo["full_name"],
        "stargazers_count": repo["stargazers_count"],
        "language": repo["language"],
        "total_lines_changed": aggregated["total_lines_changed"],
        "avg_loc": aggregated["avg_loc"],
        "contributor_count": aggregated["contributor_count"],
        "extraction_date": datetime.now().isoformat()
    }
    
    # Cleanup
    shutil.rmtree(repo_path)
    return result

def run_data_extraction(min_stars: int = 500, min_age_days: int = 730, language: str = "Python", output_path: Optional[Path] = None) -> Path:
    """
    Main entry point for data extraction: query, clone, extract, and save metadata.
    """
    config = get_config_summary()
    work_dir = Path(config["work_dir"]) / "cloned_repos"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    if output_path is None:
        output_path = Path(config["data_raw_dir"]) / "repos_metadata.csv"
    
    ensure_directories([output_path.parent])
    
    repos = query_github_repos(min_stars=min_stars, min_age_days=min_age_days, language=language)
    if not repos:
        logger.warning("No repositories found. Creating empty metadata file.")
        pd.DataFrame(columns=["repo_id", "full_name", "stargazers_count", "language", "total_lines_changed", "avg_loc", "contributor_count", "extraction_date"]).to_csv(output_path, index=False)
        return output_path
    
    results = []
    for repo in repos:
        result = process_single_repo(repo, work_dir)
        if result:
            results.append(result)
    
    save_repos_metadata(results, output_path)
    return output_path

def run_data_extraction_wrapper() -> Path:
    """
    Wrapper for main pipeline integration.
    """
    config = get_config_summary()
    return run_data_extraction(
        min_stars=config.get("min_stars", 500),
        min_age_days=config.get("min_repo_age_days", 730),
        language=config.get("target_language", "Python"),
        output_path=Path(config["data_raw_dir"]) / "repos_metadata.csv"
    )

def main():
    pin_random_seed(42)
    output_path = run_data_extraction_wrapper()
    logger.info(f"Data extraction complete. Output: {output_path}")

if __name__ == "__main__":
    main()
