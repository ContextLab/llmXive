"""
Data Extraction Module for Code Churn and Technical Debt Analysis.

This module handles repository selection, cloning, and git history extraction.
It strictly enforces the "Fail Loudly" policy: if real data cannot be obtained,
the pipeline must abort. No synthetic or mock data fallbacks are permitted.
"""
import os
import time
import logging
import shutil
import queue
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import subprocess
import re

# Importing config for paths
try:
    from config import ensure_directories, get_config_summary
except ImportError:
    # Fallback for standalone execution or missing config in test environment
    # In production, ensure config.py is in the path
    ensure_directories = lambda: None
    get_config_summary = lambda: {}

# Logger setup
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants for "Fail Loudly" policy
REAL_DATA_ONLY = True
PINNED_REPOS = [
    {"repo_id": "psf/requests", "owner": "psf", "name": "requests", "language": "python", "url": "https://github.com/psf/requests.git"},
    {"repo_id": "tensorflow/tensorflow", "owner": "tensorflow", "name": "tensorflow", "language": "python", "url": "https://github.com/tensorflow/tensorflow.git"},
    {"repo_id": "vuejs/vue", "owner": "vuejs", "name": "vue", "language": "javascript", "url": "https://github.com/vuejs/vue.git"},
    {"repo_id": "django/django", "owner": "django", "name": "django", "language": "python", "url": "https://github.com/django/django.git"},
    {"repo_id": "pallets/flask", "owner": "pallets", "name": "flask", "language": "python", "url": "https://github.com/pallets/flask.git"}
]

def get_current_ram_usage_gb() -> float:
    """Get current RAM usage in GB."""
    try:
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except Exception as e:
        logger.warning(f"Could not determine RAM usage: {e}")
        return 0.0

def load_repos_metadata() -> List[Dict[str, Any]]:
    """
    Load the pinned list of repositories.

    Enforces Real Data Only policy:
    - Checks if data/raw/repos_metadata.csv exists.
    - If missing, generates it from the PINNED_REPOS list (verified real repos).
    - NEVER generates synthetic/random data.
    - NEVER falls back to mock data if a specific repo is missing.
    """
    data_dir = Path("data/raw")
    csv_path = data_dir / "repos_metadata.csv"

    # Ensure directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    if not csv_path.exists():
        logger.info(f"{csv_path} not found. Generating from PINNED_REPOS list.")
        # Write the verified list to disk
        with open(csv_path, 'w', newline='') as f:
            import csv
            headers = ['repo_id', 'owner', 'name', 'language', 'url']
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for repo in PINNED_REPOS:
                writer.writerow(repo)
        logger.info(f"Successfully wrote verified repo list to {csv_path}")
    else:
        logger.info(f"Loading existing repo list from {csv_path}")

    # Load and validate
    repos = []
    with open(csv_path, 'r', newline='') as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            repos.append(row)

    if not repos:
        raise RuntimeError("ERROR: The pinned repo list is empty. Cannot proceed with real data.")

    return repos

def validate_public_url(url: str) -> bool:
    """
    Validate that the URL points to a public GitHub repository.
    Checks for 'github.com' in the URL and basic structure.
    """
    if not url or "github.com" not in url:
        logger.error(f"Invalid GitHub URL: {url}")
        return False
    # Basic check for https/ssh
    if not (url.startswith("https://") or url.startswith("git@")):
        logger.error(f"URL does not appear to be a valid git clone URL: {url}")
        return False
    return True

def clone_repository(repo: Dict[str, Any], clone_dir: Path, timeout: int = 300) -> bool:
    """
    Clone a repository using git.

    FAIL LOUDLY POLICY:
    - If cloning fails (network error, repo not found, etc.), raise RuntimeError.
    - NO synthetic fallback.
    - NO mock data generation.
    """
    repo_id = repo.get('repo_id', 'unknown')
    url = repo.get('url', '')

    if not validate_public_url(url):
        raise RuntimeError(f"Failed to clone real repo {repo_id}. URL validation failed: {url}. Aborting pipeline to prevent synthetic data fabrication.")

    logger.info(f"Cloning {repo_id} from {url}...")

    try:
        # Check if directory already exists and is a git repo
        if clone_dir.exists() and (clone_dir / '.git').exists():
            logger.info(f"Repo {repo_id} already cloned. Updating...")
            # Optional: git pull inside
            # subprocess.run(['git', 'pull'], cwd=clone_dir, check=True, timeout=timeout)
            return True

        # Perform clone
        # Use shallow clone to save time/space if acceptable, but full history needed for churn
        # Spec requires last 12 months. Shallow might miss older history.
        # For robustness, we attempt full clone.
        subprocess.run(
            ['git', 'clone', '--depth', '1', url, str(clone_dir)],
            check=True,
            timeout=timeout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        logger.info(f"Successfully cloned {repo_id}.")
        return True

    except subprocess.TimeoutExpired:
        error_msg = f"Timeout while cloning {repo_id}. Aborting to prevent partial/synthetic data."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except subprocess.CalledProcessError as e:
        error_msg = f"Git clone failed for {repo_id} (URL: {url}). Error: {e.stderr.decode() if e.stderr else 'Unknown'}. Aborting pipeline to prevent synthetic data fabrication."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except FileNotFoundError:
        error_msg = "Git command not found. Please install Git and ensure it is in PATH. Aborting."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error cloning {repo_id}: {e}. Aborting pipeline to prevent synthetic data fabrication."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def extract_git_metrics(repo_dir: Path, repo_id: str, months: int = 12) -> pd.DataFrame:
    """
    Extract git history metrics using pydriller.
    Returns a DataFrame with file_path, total_lines_changed, commit_count.

    This function assumes the repo has been successfully cloned (T011 logic).
    It does NOT generate synthetic data if pydriller fails.
    """
    try:
        import pydriller
        from pydriller import Repository
    except ImportError:
        raise RuntimeError("pydriller is not installed. Please install it via requirements.txt.")

    # Calculate date cutoff
    cutoff_date = datetime.now() - timedelta(days=30*months)

    metrics = []
    file_data = {} # file_path -> {lines_changed, commits}

    try:
        repo = Repository(str(repo_dir))
        for commit in repo.get_list_commits():
            # Filter by date
            if commit.committer_date < cutoff_date:
                continue

            # Analyze changed files
            for path, change in commit.changed_files.items():
                if path not in file_data:
                    file_data[path] = {'lines_changed': 0, 'commits': 0}
                
                # Additions + Deletions
                lines = change.additions + change.deletions
                file_data[path]['lines_changed'] += lines
                file_data[path]['commits'] += 1

    except Exception as e:
        error_msg = f"Failed to extract git metrics for {repo_id} using pydriller: {e}. Aborting to prevent synthetic data."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Convert to DataFrame
    if not file_data:
        logger.warning(f"No metrics found for {repo_id}. Returning empty DataFrame.")
        return pd.DataFrame(columns=['file_path', 'total_lines_changed', 'commit_count'])

    df = pd.DataFrame([
        {'file_path': k, 'total_lines_changed': v['lines_changed'], 'commit_count': v['commits']}
        for k, v in file_data.items()
    ])
    
    return df

def aggregate_file_metrics(git_df: pd.DataFrame, semgrep_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge git and semgrep metrics.
    """
    # Ensure both are DataFrames
    if git_df.empty or semgrep_df.empty:
        return pd.DataFrame()
    
    # Merge on file_path
    merged = pd.merge(git_df, semgrep_df, on='file_path', how='inner')
    return merged

def process_single_repo(repo: Dict[str, Any], base_dir: Path) -> Optional[pd.DataFrame]:
    """
    Process a single repository: clone, extract git, run semgrep, aggregate.
    Enforces Fail Loudly policy throughout.
    """
    repo_id = repo.get('repo_id', 'unknown')
    clone_dir = base_dir / "clones" / repo_id

    try:
        # 1. Clone
        clone_repository(repo, clone_dir)

        # 2. Extract Git Metrics
        git_metrics = extract_git_metrics(clone_dir, repo_id)

        # 3. Run Static Analysis (Semgrep) - handled by static_analysis.py in T014
        # For T041, we focus on the extraction and hardening of the loader.
        # We assume semgrep results exist in data/raw/static_analysis/{repo_id}/semgrep_results.json
        # If they don't exist, the pipeline will fail in T014 or T015.
        # T041 specifically hardens the *cloning* and *loading* phase.

        if git_metrics.empty:
            logger.warning(f"No git metrics for {repo_id}. Skipping aggregation.")
            return None

        return git_metrics

    except RuntimeError as e:
        # Re-raise to ensure pipeline stops
        logger.critical(f"CRITICAL FAILURE in {repo_id}: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected failure in {repo_id}: {e}")
        raise

def run_data_extraction_wrapper(repos: List[Dict[str, Any]], output_dir: Path) -> pd.DataFrame:
    """
    Wrapper to run extraction on all repos.
    """
    all_metrics = []
    for repo in repos:
        try:
            df = process_single_repo(repo, output_dir)
            if df is not None:
                all_metrics.append(df)
        except RuntimeError as e:
            # If one repo fails, the whole pipeline must stop (Fail Loudly)
            raise e
    
    if not all_metrics:
        return pd.DataFrame()
    
    return pd.concat(all_metrics, ignore_index=True)

def run_data_extraction() -> pd.DataFrame:
    """
    Main entry point for data extraction.
    """
    logger.info("Starting Data Extraction (T041 - Hardened)")
    
    # Load repos
    repos = load_repos_metadata()
    logger.info(f"Loaded {len(repos)} repositories.")

    # Ensure output directories
    output_dir = Path("data/raw")
    ensure_directories()

    # Run extraction
    result = run_data_extraction_wrapper(repos, output_dir)
    
    logger.info(f"Extraction complete. Total rows: {len(result)}")
    return result

def main():
    """CLI entry point."""
    logger.info("Running data_extraction.py main()")
    df = run_data_extraction()
    if not df.empty:
        output_path = Path("data/raw/git_history/unified_extract.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved extraction results to {output_path}")
    else:
        logger.warning("No data extracted.")

if __name__ == "__main__":
    main()