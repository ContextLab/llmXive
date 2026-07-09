import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone

from ..utils.logging import get_logger

logger = get_logger(__name__)

def clone_repository(repo_url: str, dest_dir: Optional[Path] = None) -> Path:
    """
    Clones a git repository to a temporary or specified directory.
    
    Args:
        repo_url: URL of the git repository.
        dest_dir: Optional destination directory. If None, creates a temp dir.
    
    Returns:
        Path to the cloned repository directory.
    
    Raises:
        subprocess.CalledProcessError: If cloning fails.
    """
    if dest_dir is None:
        dest_dir = Path(tempfile.mkdtemp(prefix="llmxive_repo_"))
    
    logger.info(f"Cloning {repo_url} to {dest_dir}")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1000", repo_url, str(dest_dir)],
            check=True,
            capture_output=True,
            text=True
        )
        return dest_dir
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to clone repository: {e.stderr}")
        raise

def get_file_commits(repo_path: Path, file_path: str) -> List[Dict[str, Any]]:
    """
    Retrieves commit history for a specific file in the repository.
    
    Args:
        repo_path: Path to the local git repository.
        file_path: Relative path of the file within the repo.
    
    Returns:
        List of dicts containing commit hash and timestamp.
    """
    commits = []
    try:
        # Get log with format: hash timestamp
        # Using --follow to track renames if necessary, though basic history is usually enough
        result = subprocess.run(
            [
                "git", "-C", str(repo_path), "log", "--follow", 
                "--format=%H %ct", "--", file_path
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if not line.strip():
                continue
            parts = line.split(' ')
            if len(parts) >= 2:
                commit_hash = parts[0]
                timestamp = int(parts[1])
                commits.append({
                    "hash": commit_hash,
                    "timestamp": timestamp,
                    "datetime": datetime.fromtimestamp(timestamp, tz=timezone.utc)
                })
    except subprocess.CalledProcessError as e:
        logger.warning(f"Could not retrieve history for {file_path}: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout retrieving history for {file_path}")
    
    return commits

def get_repo_commit_date(repo_path: Path) -> Optional[datetime]:
    """
    Gets the date of the most recent commit in the repository.
    
    Args:
        repo_path: Path to the local git repository.
    
    Returns:
        datetime of the latest commit or None if no commits found.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", "-1", "--format=%ct"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        timestamp = int(result.stdout.strip())
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        return None

def calculate_median_commit_age(file_commits: List[Dict[str, Any]], reference_date: Optional[datetime] = None) -> Optional[float]:
    """
    Calculates the median age of a file in days based on its commit history.
    
    The age is calculated as the difference between the reference date (usually now or repo head)
    and the commit date. If a file has sparse history (very few commits), we handle edge cases.
    
    Args:
        file_commits: List of commit dicts with 'datetime' keys.
        reference_date: The date to calculate age from. Defaults to now.
    
    Returns:
        Median age in days as a float, or None if insufficient data.
    """
    if not file_commits:
        logger.debug("No commits found for file")
        return None
    
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)
    
    ages_days = []
    for commit in file_commits:
        if "datetime" not in commit:
            continue
        age_delta = reference_date - commit["datetime"]
        ages_days.append(age_delta.total_seconds() / (24 * 3600))
    
    if not ages_days:
        return None
    
    # Sort ages to find median
    ages_days.sort()
    n = len(ages_days)
    if n % 2 == 1:
        median_age = ages_days[n // 2]
    else:
        median_age = (ages_days[n // 2 - 1] + ages_days[n // 2]) / 2.0
    
    return median_age

def process_file_history(repo_path: Path, file_path: str, reference_date: Optional[datetime] = None) -> Optional[float]:
    """
    Orchestrates getting file commits and calculating median age.
    
    Args:
        repo_path: Path to the repository.
        file_path: Path to the file within the repo.
        reference_date: Reference date for age calculation.
    
    Returns:
        Median commit age in days or None.
    """
    commits = get_file_commits(repo_path, file_path)
    if not commits:
        return None
    
    return calculate_median_commit_age(commits, reference_date)

def extract_file_age_from_url(repo_url: str, file_path: str) -> Optional[float]:
    """
    High-level function to clone (or use temp), get history, and calculate age for a file.
    
    Args:
        repo_url: URL of the repository.
        file_path: Path to the file.
    
    Returns:
        Median commit age in days or None.
    """
    temp_dir = None
    try:
        temp_dir = clone_repository(repo_url)
        return process_file_history(temp_dir, file_path)
    except Exception as e:
        logger.error(f"Error processing {file_path} from {repo_url}: {e}")
        return None
    finally:
        if temp_dir and temp_dir.exists():
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

def get_all_files_in_repo(repo_path: Path) -> List[str]:
    """
    Lists all tracked files in the repository.
    
    Args:
        repo_path: Path to the repository.
    
    Returns:
        List of relative file paths.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "ls-files"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip().split('\n')
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []

def main():
    """
    CLI entry point for testing git_utils functions.
    Usage: python -m extraction.git_utils --repo <url> --file <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Git Utils CLI")
    parser.add_argument("--repo", type=str, required=True, help="Repository URL")
    parser.add_argument("--file", type=str, required=True, help="File path in repo")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    setup_logging = get_logger("extraction.git_utils")
    logger.setLevel(args.log_level.upper())
    
    age = extract_file_age_from_url(args.repo, args.file)
    
    if age is not None:
        print(f"Median commit age for {args.file}: {age:.2f} days")
    else:
        print(f"Could not determine age for {args.file}")

if __name__ == "__main__":
    main()