import os
import time
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv

from pydriller import Repository
from config import get_config_summary, ensure_directories
from utils import get_logger, pin_random_seed

# Ensure we have a logger
logger = get_logger(__name__)

def query_github_repos() -> List[Dict[str, Any]]:
    """
    Query GitHub API for repositories.
    Note: This is a placeholder for the actual API call logic.
    In a real implementation, this would use requests to query GitHub API.
    For this task, we assume repos_metadata.csv already exists from T010.
    """
    # This function is defined for API surface compatibility but T010 handles the actual data loading
    logger.warning("query_github_repos called but T010 should have populated repos_metadata.csv")
    return []

def verify_repo_publicity(repos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Verify repository public status.
    Note: T010a handles the actual filtering.
    """
    return [r for r in repos if r.get('is_public', True)]

def save_repos_metadata(repos: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save repository metadata to CSV.
    """
    if not repos:
        logger.warning("No repositories to save.")
        return
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=repos[0].keys())
        writer.writeheader()
        writer.writerows(repos)

def clone_repository(repo_info: Dict[str, Any], target_dir: Path, timeout_seconds: int = 300) -> bool:
    """
    Clone a repository from GitHub to the target directory.
    """
    repo_url = repo_info.get('clone_url') or f"https://github.com/{repo_info['owner']}/{repo_info['name']}.git"
    repo_id = repo_info['repo_id']
    repo_path = target_dir / repo_id

    if repo_path.exists():
        logger.info(f"Repository {repo_id} already exists at {repo_path}. Skipping clone.")
        return True

    repo_path.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Cloning {repo_id} from {repo_url}...")
        # Using git clone via subprocess for robustness
        import subprocess
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
        if result.returncode != 0:
            logger.error(f"Failed to clone {repo_id}: {result.stderr}")
            return False
        logger.info(f"Successfully cloned {repo_id}.")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout while cloning {repo_id}.")
        return False
    except Exception as e:
        logger.error(f"Error cloning {repo_id}: {e}")
        return False

def extract_git_metrics(repo_path: Path, repo_id: str, months: int = 12) -> List[Dict[str, Any]]:
    """
    Use pydriller to extract per-file commit counts and lines changed.
    Returns a list of dicts: {'file_path': str, 'total_lines_changed': int, 'commit_count': int}
    """
    logger.info(f"Extracting git metrics for {repo_id} from {repo_path}...")
    
    file_metrics: Dict[str, Dict[str, int]] = {}
    
    # Calculate cutoff date (approximate)
    # Pydriller handles date filtering internally via 'from_date'
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=months * 30)

    try:
        # Initialize Repository object
        repo = Repository(str(repo_path), from_date=cutoff_date)
        
        for commit in repo.get_commits():
            for modified_file in commit.modified_files:
                # Handle file path normalization
                file_path = modified_file.filename
                if not file_path:
                    continue
                
                # Get changes (additions + deletions)
                # Pydriller's ModifiedFile has 'added' and 'deleted' properties
                added = modified_file.added
                deleted = modified_file.deleted
                total_changed = added + deleted

                if file_path not in file_metrics:
                    file_metrics[file_path] = {'total_lines_changed': 0, 'commit_count': 0}
                
                file_metrics[file_path]['total_lines_changed'] += total_changed
                file_metrics[file_path]['commit_count'] += 1
                
        logger.info(f"Extracted metrics for {len(file_metrics)} files in {repo_id}.")
    except Exception as e:
        logger.error(f"Error extracting git metrics for {repo_id}: {e}")
        # If pydriller fails (e.g., repo is too large or corrupt), return empty
        return []

    return [
        {
            'file_path': path,
            'total_lines_changed': data['total_lines_changed'],
            'commit_count': data['commit_count']
        }
        for path, data in file_metrics.items()
    ]

def aggregate_file_metrics(metrics_list: List[Dict[str, Any]], repo_id: str, output_dir: Path) -> Path:
    """
    Save aggregated file metrics to CSV.
    Returns the path to the saved CSV file.
    """
    if not metrics_list:
        logger.warning(f"No metrics to save for {repo_id}.")
        # Create an empty file with headers to satisfy schema
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / 'commits.csv'
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['file_path', 'total_lines_changed', 'commit_count'])
            writer.writeheader()
        return output_path

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'commits.csv'

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['file_path', 'total_lines_changed', 'commit_count'])
        writer.writeheader()
        writer.writerows(metrics_list)

    logger.info(f"Saved git metrics for {repo_id} to {output_path}.")
    return output_path

def process_single_repo(repo_info: Dict[str, Any], config: Dict[str, Any]) -> Optional[Path]:
    """
    Process a single repository: clone, extract metrics, save results.
    """
    repo_id = repo_info['repo_id']
    config_dirs = get_config_summary()
    git_history_dir = Path(config_dirs['data_raw']) / 'git_history'
    clone_target = Path(config_dirs['temp_clones']) / repo_id

    # Ensure directories exist
    ensure_directories()

    # Clone
    if not clone_repository(repo_info, clone_target, timeout_seconds=300):
        logger.error(f"Skipping {repo_id} due to clone failure.")
        return None

    # Extract
    metrics = extract_git_metrics(clone_target, repo_id, months=12)

    # Aggregate and Save
    repo_output_dir = git_history_dir / repo_id
    output_path = aggregate_file_metrics(metrics, repo_id, repo_output_dir)

    # Cleanup clone (optional, but good for disk space)
    # shutil.rmtree(clone_target, ignore_errors=True)

    return output_path

def run_data_extraction() -> List[Path]:
    """
    Main entry point for T011: Git History extraction.
    Reads repos from data/raw/repos_metadata.csv (output of T010).
    Outputs to data/raw/git_history/{repo_id}/commits.csv.
    """
    config = get_config_summary()
    ensure_directories()
    pin_random_seed()

    repos_csv_path = Path(config['data_raw']) / 'repos_metadata.csv'
    if not repos_csv_path.exists():
        raise FileNotFoundError(f"Required input file not found: {repos_csv_path}. Run T010 first.")

    logger.info(f"Reading repositories from {repos_csv_path}...")
    repos = []
    with open(repos_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            repos.append(row)

    if not repos:
        raise ValueError("No repositories found in repos_metadata.csv.")

    logger.info(f"Processing {len(repos)} repositories...")
    output_paths = []

    for repo_info in repos:
        try:
            result_path = process_single_repo(repo_info, config)
            if result_path:
                output_paths.append(result_path)
        except Exception as e:
            logger.error(f"Failed to process {repo_info['repo_id']}: {e}")
            continue

    logger.info(f"Git history extraction complete. {len(output_paths)} files generated.")
    return output_paths

def run_data_extraction_wrapper() -> None:
    """
    Wrapper for orchestration purposes.
    """
    run_data_extraction()

def main():
    """
    CLI entry point.
    """
    logger.info("Starting Git History Extraction (T011)...")
    run_data_extraction_wrapper()
    logger.info("Git History Extraction finished.")

if __name__ == '__main__':
    main()
