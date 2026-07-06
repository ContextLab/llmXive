"""
Git utilities for fetching history and calculating median commit age per file.

This module handles git operations including cloning repositories, traversing
commit history for specific files, and calculating the median age of commits.
It includes robust handling for sparse history edge cases (e.g., files added
late in a repo's life, or repos with no history for certain files).
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone

import git

from utils.logging import get_logger
from utils.config import ensure_directories

logger = get_logger(__name__)

# Default timeout for git operations (seconds)
GIT_OPERATION_TIMEOUT = 300
# Minimum number of commits required to calculate a meaningful median
MIN_COMMITS_FOR_MEDIAN = 1


def clone_repository(repo_url: str, target_dir: Optional[Path] = None) -> Path:
    """
    Clone a git repository to a temporary or specified directory.
    
    Args:
        repo_url: URL of the git repository to clone.
        target_dir: Optional target directory. If None, creates a temporary directory.
        
    Returns:
        Path to the cloned repository directory.
        
    Raises:
        RuntimeError: If cloning fails.
    """
    if target_dir is None:
        # Create a temporary directory for this clone
        target_dir = Path(tempfile.mkdtemp(prefix="llmxive_repo_"))
    
    logger.info(f"Cloning repository {repo_url} to {target_dir}")
    
    try:
        # Use gitpython to clone
        repo = git.Repo.clone_from(
            repo_url,
            str(target_dir),
            depth=1000,  # Limit depth to avoid massive repos, but get enough history
            single_branch=True
        )
        logger.info(f"Successfully cloned {repo_url}")
        return target_dir
    except git.exc.GitCommandError as e:
        logger.error(f"Failed to clone repository {repo_url}: {e}")
        raise RuntimeError(f"Git clone failed for {repo_url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error cloning {repo_url}: {e}")
        raise RuntimeError(f"Unexpected error cloning {repo_url}: {e}")


def get_file_commits(repo_path: Path, file_path: str) -> List[Dict[str, Any]]:
    """
    Get all commits that modified a specific file in a repository.
    
    Args:
        repo_path: Path to the local git repository.
        file_path: Relative path to the file within the repository.
        
    Returns:
        List of dictionaries containing commit information:
        - commit_hash: SHA of the commit
        - commit_date: datetime object of the commit
        - author: Author name
        - message: Commit message
        
    Returns empty list if file has no history or repository is invalid.
    """
    try:
        repo = git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError:
        logger.warning(f"Not a valid git repository: {repo_path}")
        return []
    except Exception as e:
        logger.error(f"Error opening repository {repo_path}: {e}")
        return []
    
    commits = []
    file_path_str = str(file_path)
    
    try:
        # Get commits for the specific file
        # Using git log to get history for this file
        log_output = repo.git.log(
            '--pretty=format:%H|%cI|%an|%s',
            '--follow',  # Follow renames
            '--',
            file_path_str
        )
        
        if not log_output.strip():
            logger.debug(f"No commit history found for file: {file_path_str}")
            return []
        
        for line in log_output.split('\n'):
            if not line.strip():
                continue
            
            parts = line.split('|', 3)
            if len(parts) < 4:
                continue
            
            commit_hash = parts[0]
            commit_date_str = parts[1]
            author = parts[2]
            message = parts[3]
            
            # Parse ISO format date
            try:
                commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Could not parse date for commit {commit_hash}: {commit_date_str}")
                continue
            
            commits.append({
                'commit_hash': commit_hash,
                'commit_date': commit_date,
                'author': author,
                'message': message
            })
            
    except git.exc.GitCommandError as e:
        logger.warning(f"Git log failed for file {file_path_str} in {repo_path}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting commits for {file_path_str}: {e}")
        return []
    
    return commits


def calculate_median_commit_age(commits: List[Dict[str, Any]], reference_date: Optional[datetime] = None) -> Optional[float]:
    """
    Calculate the median commit age in days for a list of commits.
    
    Args:
        commits: List of commit dictionaries with 'commit_date' field.
        reference_date: Reference date for age calculation. Defaults to now.
        
    Returns:
        Median age in days (float), or None if not enough commits.
        
    Edge Cases:
        - Empty commits list: Returns None
        - Single commit: Returns age of that commit
        - Sparse history: Handles gracefully by returning median of available data
    """
    if not commits:
        logger.debug("No commits provided, returning None for median age")
        return None
    
    if reference_date is None:
        reference_date = datetime.now(timezone.utc)
    
    # Calculate ages in days for each commit
    ages_days = []
    for commit in commits:
        commit_date = commit['commit_date']
        
        # Ensure timezone awareness
        if commit_date.tzinfo is None:
            commit_date = commit_date.replace(tzinfo=timezone.utc)
        
        age_delta = reference_date - commit_date
        age_days = age_delta.total_seconds() / (24 * 3600)
        ages_days.append(age_days)
    
    if not ages_days:
        return None
    
    # Sort ages to find median
    ages_days.sort()
    n = len(ages_days)
    
    if n == 1:
        median_age = ages_days[0]
    else:
        mid = n // 2
        if n % 2 == 0:
            median_age = (ages_days[mid - 1] + ages_days[mid]) / 2
        else:
            median_age = ages_days[mid]
    
    logger.debug(f"Calculated median commit age: {median_age:.2f} days from {n} commits")
    return median_age


def get_repo_commit_date(repo_path: Path) -> Optional[datetime]:
    """
    Get the most recent commit date for the repository (HEAD).
    
    Args:
        repo_path: Path to the git repository.
        
    Returns:
        Datetime of the most recent commit, or None if unavailable.
    """
    try:
        repo = git.Repo(repo_path)
        head_commit = repo.head.commit
        return head_commit.committed_datetime
    except Exception as e:
        logger.warning(f"Could not get repo commit date for {repo_path}: {e}")
        return None


def process_file_history(repo_path: Path, file_path: str, reference_date: Optional[datetime] = None) -> Tuple[Optional[float], int]:
    """
    Process the git history for a single file and calculate median commit age.
    
    This is the main entry point for calculating age metrics for a file.
    
    Args:
        repo_path: Path to the git repository.
        file_path: Relative path to the file.
        reference_date: Reference date for age calculation.
        
    Returns:
        Tuple of (median_age_days, commit_count)
        - median_age_days: Float or None if insufficient history
        - commit_count: Number of commits found for this file
    """
    commits = get_file_commits(repo_path, file_path)
    commit_count = len(commits)
    
    if commit_count < MIN_COMMITS_FOR_MEDIAN:
        logger.debug(f"File {file_path} has only {commit_count} commits, insufficient for median calculation")
        return None, commit_count
    
    median_age = calculate_median_commit_age(commits, reference_date)
    return median_age, commit_count


def extract_file_age_from_url(repo_url: str, file_path: str, clone_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    High-level function to extract file age information from a repository URL.
    
    This function clones the repo (if needed), extracts commit history for the file,
    and calculates the median commit age.
    
    Args:
        repo_url: URL of the git repository.
        file_path: Relative path to the file within the repo.
        clone_dir: Optional directory to clone to. If None, uses temp directory.
        
    Returns:
        Dictionary with keys:
        - repo_url: The repository URL
        - file_path: The file path
        - median_commit_age: Median age in days (float or None)
        - commit_count: Number of commits found
        - status: 'success', 'sparse_history', 'no_history', or 'error'
        - error_message: Error details if any (only if status is 'error')
    """
    result = {
        'repo_url': repo_url,
        'file_path': file_path,
        'median_commit_age': None,
        'commit_count': 0,
        'status': 'error',
        'error_message': None
    }
    
    temp_dir = None
    try:
        # Clone repository if not provided
        if clone_dir is None:
            temp_dir = Path(tempfile.mkdtemp(prefix="llmxive_age_calc_"))
            repo_path = clone_repository(repo_url, temp_dir)
        else:
            repo_path = clone_dir
        
        # Get reference date (most recent commit in repo)
        reference_date = get_repo_commit_date(repo_path)
        
        # Process file history
        median_age, commit_count = process_file_history(repo_path, file_path, reference_date)
        
        result['commit_count'] = commit_count
        result['median_commit_age'] = median_age
        
        if commit_count == 0:
            result['status'] = 'no_history'
            logger.info(f"No commit history for {file_path} in {repo_url}")
        elif median_age is None:
            result['status'] = 'sparse_history'
            logger.info(f"Sparse history for {file_path} in {repo_url}: {commit_count} commits")
        else:
            result['status'] = 'success'
            logger.info(f"Calculated median age {median_age:.2f} days for {file_path} ({commit_count} commits)")
            
    except Exception as e:
        result['status'] = 'error'
        result['error_message'] = str(e)
        logger.error(f"Error processing {file_path} from {repo_url}: {e}")
    finally:
        # Clean up temporary directory if we created one
        if temp_dir and temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to remove temp directory {temp_dir}: {e}")
    
    return result


def get_all_files_in_repo(repo_path: Path, extensions: Optional[List[str]] = None) -> List[str]:
    """
    Get all files in a repository, optionally filtered by extension.
    
    Args:
        repo_path: Path to the git repository.
        extensions: Optional list of file extensions to filter (e.g., ['.py']).
        
    Returns:
        List of relative file paths.
    """
    try:
        repo = git.Repo(repo_path)
        tree = repo.tree()
        files = []
        
        for blob in tree.traverse():
            if blob.type == 'blob':
                file_path = str(blob.path)
                
                if extensions:
                    ext_lower = file_path.split('.')[-1].lower()
                    if f'.{ext_lower}' not in extensions:
                        continue
                
                files.append(file_path)
        
        return files
    except Exception as e:
        logger.error(f"Error listing files in {repo_path}: {e}")
        return []


def main():
    """
    Command-line interface for testing git_utils functionality.
    
    Usage:
        python -m code.extraction.git_utils <repo_url> <file_path>
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python -m code.extraction.git_utils <repo_url> <file_path>")
        sys.exit(1)
    
    repo_url = sys.argv[1]
    file_path = sys.argv[2]
    
    logger.info(f"Testing git_utils with repo: {repo_url}, file: {file_path}")
    
    result = extract_file_age_from_url(repo_url, file_path)
    
    print(f"Result: {result}")
    
    if result['status'] == 'success':
        print(f"Median commit age: {result['median_commit_age']:.2f} days")
        print(f"Commit count: {result['commit_count']}")
    elif result['status'] == 'sparse_history':
        print(f"Sparse history: {result['commit_count']} commits found")
        print(f"Median age: {result['median_commit_age']}")
    elif result['status'] == 'no_history':
        print(f"No commit history found for {file_path}")
    else:
        print(f"Error: {result['error_message']}")

if __name__ == '__main__':
    main()