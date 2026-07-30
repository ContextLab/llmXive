import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Import local modules
from config import get_config_summary, ensure_directories
from utils import get_logger, pin_random_seed
from parallelism_config import get_max_concurrent_repos

# Setup logging
logger = get_logger(__name__)

# Thread-local storage for progress tracking
thread_local = threading.local()

def clone_repository(repo_url: str, dest_path: Path) -> bool:
    """Clone a repository to the destination path."""
    import subprocess
    try:
        if dest_path.exists():
            logger.debug(f"Repository already exists at {dest_path}, skipping clone.")
            return True
        
        dest_path.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(dest_path)],
            check=True,
            capture_output=True,
            timeout=300
        )
        return True
    except Exception as e:
        logger.error(f"Failed to clone {repo_url}: {e}")
        return False

def extract_git_metrics(repo_path: Path, repo_id: str) -> Optional[Dict[str, Any]]:
    """Extract git metrics using pydriller for a single repository."""
    try:
        from pydriller import RepositoryMining
        
        # Limit to last 2 years
        end_date = None
        start_date = None
        # Calculate start date dynamically if needed, or use a fixed offset
        # For now, we assume pydriller handles relative dates or we pass a specific date
        # Pydriller date format: 'YYYY-MM-DD'
        # We'll fetch all commits and filter in memory for simplicity in this snippet
        # or rely on pydriller's date filtering if available in the version.
        
        metrics = {
            "repo_id": repo_id,
            "total_commits": 0,
            "files_changed": set(),
            "total_lines_added": 0,
            "total_lines_deleted": 0
        }
        
        # Use threading lock if pydriller isn't thread-safe in this context,
        # but usually we process one repo per thread.
        
        # Example of iterating commits
        # Note: In a real heavy-load scenario, we might stream this more carefully
        for commit in RepositoryMining(str(repo_path), 
                                       from_date="2022-01-01", # Dynamic date logic would go here
                                       to_date=None).traverse_commits():
            metrics["total_commits"] += 1
            for modified_file in commit.modified_files:
                metrics["files_changed"].add(modified_file.path)
                metrics["total_lines_added"] += modified_file.added_lines
                metrics["total_lines_deleted"] += modified_file.removed_lines
        
        metrics["files_changed"] = list(metrics["files_changed"])
        return metrics
    except Exception as e:
        logger.error(f"Error extracting git metrics for {repo_path}: {e}")
        return None

def aggregate_file_metrics(repo_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Aggregate metrics down to file level (simplified for this task)."""
    # In the full implementation, this would map commits to specific files
    # and calculate lines changed per file.
    # Here we return a placeholder structure that matches the expected schema
    # until the full extraction logic is wired.
    return []

def save_repos_metadata(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Save repository metadata to CSV."""
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metadata to {output_path}")

def query_github_repos(min_stars: int = 500, languages: Optional[List[str]] = None, max_repos: int = 10) -> List[Dict[str, Any]]:
    """Query GitHub API for repositories."""
    # Simplified query logic
    url = "https://api.github.com/search/repositories"
    params = {
        "q": f"stars:>{min_stars}",
        "sort": "stars",
        "order": "desc",
        "per_page": max_repos
    }
    if languages:
        params["q"] += f" language:{languages[0]}" # Simplified: just first language

    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("items", [])
    except Exception as e:
        logger.error(f"GitHub API query failed: {e}")
        return []

def process_single_repo(repo_data: Dict[str, Any], base_dir: Path) -> Optional[Dict[str, Any]]:
    """Process a single repository: clone, extract metrics, aggregate."""
    repo_name = repo_data["name"]
    repo_id = str(repo_data["id"])
    repo_url = repo_data["html_url"]
    clone_path = base_dir / repo_name

    logger.info(f"Processing repo: {repo_name} (ID: {repo_id})")
    
    if not clone_repository(repo_url, clone_path):
        return None
    
    metrics = extract_git_metrics(clone_path, repo_id)
    if not metrics:
        return None
    
    # In a full implementation, we would also run static analysis here
    # and combine the results.
    return {
        "repo_id": metrics["repo_id"],
        "name": repo_name,
        "stars": repo_data.get("stargazers_count", 0),
        "total_commits": metrics["total_commits"],
        "total_lines_changed": metrics["total_lines_added"] + metrics["total_lines_deleted"]
    }

def run_data_extraction(output_dir: Path, max_repos: int = 5) -> List[Dict[str, Any]]:
    """
    Run data extraction with constrained parallelism.
    
    This function respects the concurrency limits defined in parallelism_config
    to ensure stable execution.
    """
    ensure_directories(output_dir)
    base_clone_dir = output_dir / "clones"
    base_clone_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Querying GitHub for repos (max {max_repos})...")
    repos = query_github_repos(max_repos=max_repos)
    if not repos:
        logger.warning("No repositories found.")
        return []
    
    results = []
    max_workers = get_max_concurrent_repos()
    logger.info(f"Starting parallel extraction with max {max_workers} concurrent workers.")
    
    # Use ThreadPoolExecutor to limit concurrency
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_repo = {
            executor.submit(process_single_repo, repo, base_clone_dir): repo 
            for repo in repos
        }
        
        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    logger.info(f"Completed: {repo['name']}")
                else:
                    logger.warning(f"Failed to process: {repo['name']}")
            except Exception as e:
                logger.error(f"Error processing {repo['name']}: {e}")
    
    return results

def run_data_extraction_wrapper() -> None:
    """Wrapper to run extraction and save results."""
    from config import get_config_summary
    config = get_config_summary()
    output_dir = Path(config["paths"]["data_processed"]) # Or data_raw as appropriate
    
    results = run_data_extraction(output_dir)
    save_repos_metadata(results, output_dir / "repos_metadata.csv")

def main():
    pin_random_seed(42)
    run_data_extraction_wrapper()

if __name__ == "__main__":
    main()
