"""
Git repository clone utility for the llmXive pipeline.

This module provides functionality to clone GitHub repositories into the
project's data/raw/repos/ directory.
"""
import os
import logging
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

from config import get_config
from utils.repo_loader import load_repo_list, RepoLoaderException

# Configure logging
logger = logging.getLogger(__name__)


class GitCloneException(Exception):
    """Exception raised when git clone operation fails."""
    pass


def clone_repository(github_url: str, target_dir: Path) -> bool:
    """
    Clone a GitHub repository to the specified target directory.

    Args:
        github_url: The GitHub URL of the repository to clone.
        target_dir: The directory where the repository should be cloned.

    Returns:
        True if the clone was successful.

    Raises:
        GitCloneException: If the clone operation fails.
    """
    # Extract repository name from URL for the target directory
    repo_name = github_url.rstrip('/').split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]

    repo_path = target_dir / repo_name

    # If repository already exists, remove it to ensure a fresh clone
    if repo_path.exists():
        logger.info(f"Removing existing repository at {repo_path}")
        shutil.rmtree(repo_path)

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Cloning {github_url} to {repo_path}")
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', github_url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout per repo
        )

        if result.returncode != 0:
            error_msg = f"Failed to clone {github_url}: {result.stderr}"
            logger.error(error_msg)
            raise GitCloneException(error_msg)

        logger.info(f"Successfully cloned {github_url}")
        return True

    except subprocess.TimeoutExpired:
        error_msg = f"Timeout cloning {github_url}"
        logger.error(error_msg)
        raise GitCloneException(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error cloning {github_url}: {str(e)}"
        logger.error(error_msg)
        raise GitCloneException(error_msg)


def clone_repos_from_list(repo_list_path: Optional[str] = None) -> List[str]:
    """
    Clone all repositories from the repo list file.

    Args:
        repo_list_path: Optional path to the repo list JSON file.
                        If None, uses the default path from config.

    Returns:
        List of successfully cloned repository paths.

    Raises:
        GitCloneException: If cloning fails for any repository.
        RepoLoaderException: If the repo list cannot be loaded.
    """
    config = get_config()
    target_base = Path(config.data_raw_dir) / "repos"

    # Load repository list
    try:
        repo_list = load_repo_list(repo_list_path)
    except RepoLoaderException as e:
        logger.error(f"Failed to load repository list: {e}")
        raise

    if not repo_list:
        logger.warning("No repositories found in the list")
        return []

    cloned_repos = []

    for repo_entry in repo_list:
        github_url = repo_entry.get('github_url')
        if not github_url:
            logger.warning(f"Skipping entry without github_url: {repo_entry}")
            continue

        try:
            clone_repository(github_url, target_base)
            cloned_repos.append(str(target_base / github_url.split('/')[-1].replace('.git', '')))
            logger.info(f"Successfully cloned {len(cloned_repos)}/{len(repo_list)} repositories")
        except GitCloneException as e:
            # Log the error but continue with other repositories
            # This allows partial completion if some repos fail
            logger.error(f"Skipping {github_url} due to clone failure: {e}")
            # In a strict pipeline, we might want to abort here:
            # raise

    return cloned_repos


def verify_repo_exists(repo_path: str) -> bool:
    """
    Verify that a cloned repository exists and contains Python files.

    Args:
        repo_path: Path to the cloned repository.

    Returns:
        True if the repository exists and is valid.
    """
    path = Path(repo_path)
    if not path.exists():
        logger.error(f"Repository path does not exist: {repo_path}")
        return False

    if not path.is_dir():
        logger.error(f"Repository path is not a directory: {repo_path}")
        return False

    # Check for at least one .py file
    py_files = list(path.rglob("*.py"))
    if not py_files:
        logger.warning(f"No Python files found in {repo_path}")
        return False

    logger.info(f"Verified repository at {repo_path} with {len(py_files)} Python files")
    return True


def main():
    """Main entry point for the git clone utility."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting repository cloning process")

    try:
        cloned = clone_repos_from_list()
        logger.info(f"Cloning complete. Successfully cloned {len(cloned)} repositories.")

        # Verify all cloned repos
        valid_count = 0
        for repo_path in cloned:
            if verify_repo_exists(repo_path):
                valid_count += 1

        logger.info(f"Verification complete. {valid_count}/{len(cloned)} repositories are valid.")

        if valid_count != len(cloned):
            logger.warning("Some repositories failed verification.")
            return 1

        return 0

    except (GitCloneException, RepoLoaderException) as e:
        logger.error(f"Pipeline failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
