import os
import time
import logging
import shutil
import queue
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_config_summary, ensure_directories
from utils import get_logger, calculate_checksum

logger = get_logger(__name__)

# Batch processing constants
BATCH_SIZE = 100
RAM_TRIGGER_GB = 5.0
QUEUE_MAXSIZE = 100

def get_current_ram_usage_gb() -> float:
    """Get current system RAM usage in GB."""
    try:
        mem = psutil.virtual_memory()
        return mem.used / (1024 ** 3)
    except Exception as e:
        logger.warning(f"Could not read RAM usage: {e}. Defaulting to 0.")
        return 0.0

def load_repos_metadata() -> List[Dict[str, Any]]:
    """Load the pinned list of repositories from data/raw/repos_metadata.csv."""
    config = get_config_summary()
    data_path = Path(config['paths']['raw_data']) / 'repos_metadata.csv'
    
    if not data_path.exists():
        logger.error(f"Repository metadata file not found: {data_path}")
        raise FileNotFoundError(f"Missing required file: {data_path}")
    
    import pandas as pd
    df = pd.read_csv(data_path)
    
    # Validate schema
    required_cols = {'repo_id', 'owner', 'name', 'language', 'url'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns in repos_metadata.csv: {missing}")
    
    return df.to_dict(orient='records')

def clone_repository(repo_info: Dict[str, Any], clone_dir: Path) -> bool:
    """Clone a repository to the specified directory."""
    repo_url = repo_info['url']
    repo_id = repo_info['repo_id']
    repo_path = clone_dir / repo_id
    
    if repo_path.exists():
        logger.info(f"Repository {repo_id} already exists at {repo_path}, skipping clone.")
        return True
    
    try:
        import git
        logger.info(f"Cloning {repo_url} to {repo_path}...")
        git.Repo.clone_from(repo_url, str(repo_path), depth=1)
        return True
    except Exception as e:
        logger.error(f"Failed to clone {repo_url}: {e}")
        return False

def extract_git_metrics(repo_path: Path, repo_id: str) -> Optional[Path]:
    """Extract git history metrics using pydriller."""
    import pandas as pd
    from pydriller import Repository
    
    output_dir = Path(get_config_summary()['paths']['raw_data']) / 'git_history' / repo_id
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'commits.csv'
    
    try:
        commits_data = []
        # Analyze last 12 months
        from datetime import datetime, timedelta
        since = datetime.now() - timedelta(days=365)
        
        repo = Repository(str(repo_path), since=since)
        
        for commit in repo.get_commits():
            for mod in commit.modifications:
                # Calculate lines changed (additions + deletions)
                lines_changed = (mod.addition or 0) + (mod.deletion or 0)
                commits_data.append({
                    'file_path': mod.path,
                    'total_lines_changed': lines_changed,
                    'commit_count': 1,
                    'commit_hash': commit.hash
                })
        
        if commits_data:
            df = pd.DataFrame(commits_data)
            # Aggregate by file
            aggregated = df.groupby('file_path').agg({
                'total_lines_changed': 'sum',
                'commit_count': 'sum'
            }).reset_index()
            aggregated.to_csv(output_file, index=False)
            logger.info(f"Git metrics saved to {output_file}")
            return output_file
        else:
            logger.warning(f"No commits found for {repo_id} in the last 12 months.")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting git metrics for {repo_id}: {e}")
        return None

def aggregate_file_metrics(repo_id: str) -> Optional[Path]:
    """Aggregate file metrics from git and static analysis (placeholder for now)."""
    # This function would merge git history with static analysis results
    # For now, we just return the git metrics path
    git_dir = Path(get_config_summary()['paths']['raw_data']) / 'git_history' / repo_id
    git_file = git_dir / 'commits.csv'
    if git_file.exists():
        return git_file
    return None

def process_single_repo(repo_info: Dict[str, Any], clone_base: Path) -> Optional[Dict[str, Any]]:
    """Process a single repository: clone, extract metrics, aggregate."""
    repo_id = repo_info['repo_id']
    logger.info(f"Processing repository: {repo_id}")
    
    # Clone
    if not clone_repository(repo_info, clone_base):
        return None
    
    repo_path = clone_base / repo_id
    
    # Extract git metrics
    git_metrics_path = extract_git_metrics(repo_path, repo_id)
    if not git_metrics_path:
        return None
    
    # Aggregate (placeholder for merging with static analysis)
    aggregated_path = aggregate_file_metrics(repo_id)
    
    return {
        'repo_id': repo_id,
        'git_metrics_path': str(git_metrics_path),
        'aggregated_path': str(aggregated_path) if aggregated_path else None
    }

def run_data_extraction_wrapper(repos: List[Dict[str, Any]], clone_base: Path) -> List[Dict[str, Any]]:
    """
    Run data extraction with batch logic.
    Uses queue.Queue with maxsize=100.
    Triggers batch processing if RAM usage > 5GB.
    """
    results = []
    repo_queue = queue.Queue(maxsize=QUEUE_MAXSIZE)
    
    # Add all repos to queue
    for repo in repos:
        repo_queue.put(repo)
    
    logger.info(f"Starting batch processing for {len(repos)} repositories.")
    logger.info(f"Queue maxsize: {QUEUE_MAXSIZE}, Batch size: {BATCH_SIZE}, RAM trigger: {RAM_TRIGGER_GB}GB")
    
    batch_count = 0
    processed_count = 0
    
    while not repo_queue.empty():
        # Check RAM usage before processing next batch
        current_ram = get_current_ram_usage_gb()
        if current_ram > RAM_TRIGGER_GB:
            logger.warning(f"RAM usage ({current_ram:.2f}GB) exceeds trigger ({RAM_TRIGGER_GB}GB). "
                           f"Pausing to allow memory to clear.")
            time.sleep(5)  # Wait briefly to let memory clear
            continue
        
        batch = []
        while len(batch) < BATCH_SIZE and not repo_queue.empty():
            try:
                repo = repo_queue.get_nowait()
                batch.append(repo)
            except queue.Empty:
                break
        
        if not batch:
            break
        
        batch_count += 1
        logger.info(f"Processing batch {batch_count} with {len(batch)} repositories.")
        
        for repo_info in batch:
            result = process_single_repo(repo_info, clone_base)
            if result:
                results.append(result)
                processed_count += 1
            
            # Yield control to allow other tasks or memory cleanup
            time.sleep(0.1)
    
    logger.info(f"Batch processing complete. Processed {processed_count} repositories.")
    return results

def run_data_extraction(repos: List[Dict[str, Any]], clone_base: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Main entry point for data extraction with batch logic."""
    if clone_base is None:
        config = get_config_summary()
        clone_base = Path(config['paths']['raw_data']) / 'clones'
    
    ensure_directories()
    clone_base.mkdir(parents=True, exist_ok=True)
    
    return run_data_extraction_wrapper(repos, clone_base)

def main():
    """Main entry point for data extraction script."""
    logger.info("Starting data extraction with batch logic.")
    
    try:
        repos = load_repos_metadata()
        results = run_data_extraction(repos)
        logger.info(f"Successfully processed {len(results)} repositories.")
    except Exception as e:
        logger.error(f"Data extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()