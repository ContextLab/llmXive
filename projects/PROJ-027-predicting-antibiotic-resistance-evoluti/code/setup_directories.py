"""
Setup script to create the core project directory structure.
Creates utils, tests, and data directories as specified in T001b.
"""
import os
import sys
from pathlib import Path
from utils.logging import get_logger

# Define the directories to create relative to the project root
DIRECTORIES_TO_CREATE = [
    "code/utils",
    "tests",
    "data/raw",
    "data/processed",
    "data/models",
]

def create_directories(base_path: Path, dirs: list) -> None:
    """
    Create a list of directories under the base path.
    Raises an error if creation fails.
    """
    logger = get_logger(__name__)
    created_count = 0
    for dir_name in dirs:
        target_path = base_path / dir_name
        if not target_path.exists():
            try:
                target_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {target_path}")
                created_count += 1
            except OSError as e:
                logger.error(f"Failed to create directory {target_path}: {e}")
                raise
        else:
            logger.debug(f"Directory already exists: {target_path}")
    
    logger.info(f"Directory creation complete. Created {created_count} new directories.")

def verify_directories(base_path: Path, dirs: list) -> bool:
    """
    Verify that all required directories exist.
    Returns True if all exist, False otherwise.
    """
    logger = get_logger(__name__)
    all_exist = True
    for dir_name in dirs:
        target_path = base_path / dir_name
        if not target_path.is_dir():
            logger.error(f"Verification failed: Directory missing - {target_path}")
            all_exist = False
        else:
            logger.debug(f"Verified: {target_path}")
    
    if all_exist:
        logger.info("All required directories verified successfully.")
    else:
        logger.error("Directory verification failed. Some directories are missing.")
    
    return all_exist

def main():
    logger = get_logger(__name__)
    logger.info("Starting directory setup (T001b)...")
    
    # Determine project root (assumed to be the parent of 'code')
    # If running from code/setup_directories.py, project root is parent of this file
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    create_directories(project_root, DIRECTORIES_TO_CREATE)
    
    if verify_directories(project_root, DIRECTORIES_TO_CREATE):
        logger.info("Task T001b completed successfully.")
        return 0
    else:
        logger.error("Task T001b failed verification.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
