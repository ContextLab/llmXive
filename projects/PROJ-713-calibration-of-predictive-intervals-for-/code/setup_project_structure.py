import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

from utils.logger import get_logger

# Constants for directory structure
REQUIRED_DIRS: List[str] = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "results",
]

logger = get_logger(__name__)


def ensure_dir_with_backoff(dir_path: Path, max_retries: int = 5, base_delay: float = 0.1) -> bool:
    """
    Ensures a directory exists with exponential backoff retry logic.

    Args:
        dir_path: The Path object for the directory to create.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds before the first retry.

    Returns:
        True if the directory exists or was successfully created, False otherwise.
    """
    delay = base_delay
    for attempt in range(max_retries):
        try:
            # Create the directory if it doesn't exist (parents=True for nested)
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Verify existence with a small buffer to handle filesystem latency
            if dir_path.is_dir():
                logger.info(f"Verified directory exists: {dir_path}")
                return True
            
            # If is_dir returns False immediately after creation, retry
            logger.warning(f"Directory created but verification failed for {dir_path}, retrying...")
            
        except OSError as e:
            logger.error(f"OS error creating directory {dir_path}: {e}")
            # If it's a permission error or similar, we might not want to retry indefinitely
            if e.errno == 13: # Permission denied
                logger.error("Permission denied. Aborting directory creation.")
                return False

        if attempt < max_retries - 1:
            logger.info(f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

    logger.error(f"Failed to verify directory {dir_path} after {max_retries} attempts.")
    return False


def setup_project_structure(root_path: Path = None) -> Tuple[bool, List[str]]:
    """
    Sets up the project directory structure with retry logic.

    Args:
        root_path: The root path of the project. Defaults to current working directory.

    Returns:
        A tuple (success, failed_dirs) where success is a boolean indicating if all
        directories were created, and failed_dirs is a list of paths that failed.
    """
    if root_path is None:
        root_path = Path.cwd()
    
    logger.info(f"Setting up project structure at: {root_path}")
    
    failed_dirs = []
    success = True

    for dir_name in REQUIRED_DIRS:
        full_path = root_path / dir_name
        logger.info(f"Processing directory: {full_path}")
        
        if not ensure_dir_with_backoff(full_path):
            failed_dirs.append(str(full_path))
            success = False
        else:
            logger.info(f"Successfully ensured directory: {full_path}")

    if success:
        logger.info("Project structure setup completed successfully.")
    else:
        logger.error(f"Project structure setup failed for directories: {failed_dirs}")

    return success, failed_dirs


def main():
    """Main entry point for running the setup script."""
    # Determine project root (usually the directory containing this script's parent or cwd)
    # For this script, we assume it runs from the project root or we pass it explicitly
    project_root = Path.cwd()
    
    logger.info("Starting project structure initialization...")
    success, failed = setup_project_structure(project_root)
    
    if not success:
        logger.error("Exiting due to directory creation failures.")
        sys.exit(1)
    
    logger.info("Initialization complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()