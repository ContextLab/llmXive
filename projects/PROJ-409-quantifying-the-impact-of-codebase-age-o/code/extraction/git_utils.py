"""
Git utilities for fetching repository history and calculating file age metrics.

This module provides functions to clone repositories, extract commit history
for specific files, and calculate the median commit age in days.
"""

import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta

from utils.logging import get_logger

logger = get_logger(__name__)


def clone_repository(repo_url: str, target_dir: Optional[Path] = None) -> Path:
    """
    Clone a git repository to a temporary or specified directory.

    Args:
        repo_url: URL of the git repository to clone.
        target_dir: Optional target directory. If None, creates a temp dir.

    Returns:
        Path to the cloned repository directory.

    Raises:
        subprocess.CalledProcessError: If cloning fails.
    """
    if target_dir is None:
        target_dir = Path(tempfile.mkdtemp(prefix="git_clone_"))
    else:
        target_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Cloning repository {repo_url} to {target_dir}")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1000", repo_url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            # Try full clone if shallow fails
            logger.warning(f"Shallow clone failed, trying full clone: {result.stderr}")
            subprocess.run(
                ["git", "clone", repo_url, str(target_dir)],
                capture_output=True,
                text=True,
                timeout=600
            )
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout cloning {repo_url}")
        raise
    except Exception as e:
        logger.error(f"Error cloning {repo_url}: {e}")
        raise

    return target_dir


def get_file_commits(repo_path: Path, file_path: str) -> List[Dict[str, Any]]:
    """
    Get commit history for a specific file in the repository.

    Args:
        repo_path: Path to the local git repository.
        file_path: Relative path of the file within the repo.

    Returns:
        List of dictionaries containing commit hash and timestamp.
    """
    commits = []
    try:
        result = subprocess.run(
            ["git", "log", "--follow", "--format=%H %ct", "--", file_path],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode != 0:
            logger.warning(f"Git log failed for {file_path}: {result.stderr}")
            return []

        lines = result.stdout.strip().split('\n')
        for line in lines:
            if not line:
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
    except subprocess.TimeoutExpired:
        logger.warning(f"Timeout getting commits for {file_path}")
    except Exception as e:
        logger.error(f"Error getting commits for {file_path}: {e}")

    return commits


def calculate_median_commit_age(commits: List[Dict[str, Any]]) -> Optional[float]:
    """
    Calculate the median age of commits in days.

    Args:
        commits: List of commit dictionaries with 'datetime' keys.

    Returns:
        Median age in days, or None if no commits exist.

    Handles sparse history by:
    - Returning None if the list is empty.
    - Using the time from the first commit to now if only one commit exists.
    - Calculating the median of intervals between commits if multiple exist.
    """
    if not commits:
        logger.debug("No commits provided for age calculation")
        return None

    now = datetime.now(timezone.utc)

    if len(commits) == 1:
        # Sparse history: single commit. Age is time since that commit.
        age_days = (now - commits[0]["datetime"]).days
        logger.debug(f"Sparse history (1 commit): age = {age_days} days")
        return float(age_days)

    # Calculate intervals between consecutive commits
    ages = []
    for i in range(len(commits)):
        commit_date = commits[i]["datetime"]
        if i == 0:
            # Age relative to now for the most recent commit
            age = (now - commit_date).days
        else:
            # Age relative to the next older commit (interval)
            next_date = commits[i - 1]["datetime"]
            age = (next_date - commit_date).days
        ages.append(age)

    ages.sort()
    n = len(ages)
    if n % 2 == 0:
        median_age = (ages[n // 2 - 1] + ages[n // 2]) / 2.0
    else:
        median_age = ages[n // 2]

    logger.debug(f"Calculated median age from {n} intervals: {median_age} days")
    return float(median_age)


def get_repo_commit_date(repo_path: Path, file_path: str) -> Optional[datetime]:
    """
    Get the date of the most recent commit for a file.

    Args:
        repo_path: Path to the local git repository.
        file_path: Relative path of the file.

    Returns:
        Most recent commit datetime, or None if no commits found.
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", file_path],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0 and result.stdout.strip():
            timestamp = int(result.stdout.strip())
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    except Exception as e:
        logger.warning(f"Could not get commit date for {file_path}: {e}")
    return None


def process_file_history(repo_path: Path, file_path: str) -> Tuple[Optional[float], int]:
    """
    Process a single file's git history to calculate median commit age.

    Args:
        repo_path: Path to the local git repository.
        file_path: Relative path of the file.

    Returns:
        Tuple of (median_age_in_days, commit_count).
        Returns (None, 0) if file has no history.
    """
    commits = get_file_commits(repo_path, file_path)
    if not commits:
        return None, 0

    median_age = calculate_median_commit_age(commits)
    return median_age, len(commits)


def extract_file_age_from_url(repo_url: str, file_path: str) -> Optional[float]:
    """
    Convenience function to clone, calculate age, and cleanup.

    Args:
        repo_url: URL of the repository.
        file_path: Path to the file within the repo.

    Returns:
        Median commit age in days, or None if calculation fails.
    """
    temp_dir = None
    try:
        temp_dir = clone_repository(repo_url)
        age, count = process_file_history(temp_dir, file_path)
        if age is not None:
            logger.info(f"File {file_path} in {repo_url} has median age {age:.2f} days ({count} commits)")
            return age
        else:
            logger.warning(f"No commit history found for {file_path} in {repo_url}")
            return None
    except Exception as e:
        logger.error(f"Failed to extract age for {file_path} from {repo_url}: {e}")
        return None
    finally:
        if temp_dir and temp_dir.exists():
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to remove temp dir {temp_dir}: {e}")


def get_all_files_in_repo(repo_path: Path) -> List[str]:
    """
    Get a list of all files in the repository.

    Args:
        repo_path: Path to the local git repository.

    Returns:
        List of relative file paths.
    """
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return [f for f in result.stdout.strip().split('\n') if f]
    except Exception as e:
        logger.error(f"Error listing files in {repo_path}: {e}")
    return []


def main():
    """
    CLI entry point for testing git utilities.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Git Age Calculator")
    parser.add_argument("--repo", type=str, required=True, help="Repository URL")
    parser.add_argument("--file", type=str, required=True, help="File path in repo")
    args = parser.parse_args()

    age = extract_file_age_from_url(args.repo, args.file)
    if age is not None:
        print(f"Median commit age: {age:.2f} days")
    else:
        print("Could not calculate age")
        exit(1)


if __name__ == "__main__":
    main()
