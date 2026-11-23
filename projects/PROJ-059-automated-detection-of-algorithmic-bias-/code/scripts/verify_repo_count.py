"""
Script to verify that data/raw contains the required number of repositories.
Task: T0412 - Pre-condition Check

This script checks if the data/raw directory exists and contains the 
expected number of repositories (500) as per the project requirements.

Usage:
    python scripts/verify_repo_count.py
    
Exit codes:
    0 - Success: Required number of repositories found
    1 - Failure: Required number of repositories not found or directory missing
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
REQUIRED_REPO_COUNT = 500
DATA_RAW_PATH = Path("data/raw")

def count_repos_in_directory(directory: Path) -> int:
    """
    Count the number of repositories in the given directory.
    
    A repository is identified as a subdirectory containing a .git directory
    or a repository-specific marker file (e.g., README.md, setup.py, pyproject.toml).
    
    Args:
        directory: Path to the directory containing repositories
        
    Returns:
        int: Number of repositories found
    """
    if not directory.exists():
        logger.error(f"Directory does not exist: {directory}")
        return 0
    
    if not directory.is_dir():
        logger.error(f"Path is not a directory: {directory}")
        return 0
    
    repo_count = 0
    
    for item in directory.iterdir():
        if item.is_dir():
            # Check if this is a git repository or has typical repo markers
            has_git = (item / ".git").exists()
            has_readme = (item / "README.md").exists()
            has_setup = (item / "setup.py").exists()
            has_pyproject = (item / "pyproject.toml").exists()
            
            # Consider it a repository if it has git or at least one marker
            if has_git or has_readme or has_setup or has_pyproject:
                repo_count += 1
    
    return repo_count

def verify_repo_count() -> bool:
    """
    Verify that the data/raw directory contains the required number of repositories.
    
    Returns:
        bool: True if verification passes, False otherwise
    """
    logger.info(f"Checking repository count in {DATA_RAW_PATH}")
    
    if not DATA_RAW_PATH.exists():
        logger.error(f"Required directory does not exist: {DATA_RAW_PATH}")
        logger.error("Please run the data acquisition script first: scripts/acquire_repo_data.py")
        return False
    
    repo_count = count_repos_in_directory(DATA_RAW_PATH)
    logger.info(f"Found {repo_count} repositories in {DATA_RAW_PATH}")
    
    if repo_count < REQUIRED_REPO_COUNT:
        logger.error(f"Insufficient repositories: found {repo_count}, required {REQUIRED_REPO_COUNT}")
        logger.error(f"Missing {REQUIRED_REPO_COUNT - repo_count} repositories")
        logger.error("Please ensure data acquisition (T006a) completed successfully")
        return False
    
    logger.info(f"SUCCESS: Repository count verification passed ({repo_count} >= {REQUIRED_REPO_COUNT})")
    return True

def main():
    """Main entry point for the verification script."""
    logger.info("=" * 60)
    logger.info("Starting repository count verification (Task T0412)")
    logger.info("=" * 60)
    
    success = verify_repo_count()
    
    if success:
        logger.info("=" * 60)
        logger.info("Verification PASSED - Ready to proceed with pipeline")
        logger.info("=" * 60)
        sys.exit(0)
    else:
        logger.info("=" * 60)
        logger.info("Verification FAILED - Prerequisites not met")
        logger.info("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()