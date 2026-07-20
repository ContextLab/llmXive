"""
Setup data directory structure for the code smell comparison study.

This script creates the required directory hierarchy under the project's
data/ folder as defined in the project plan and tasks.md.

Directories created:
- data/raw/human_samples
- data/raw/llm_samples
- data/raw/reference_set
- data/intermediate
- data/processed
- figures
"""
import os
import sys
from pathlib import Path
from utils.logger import get_logger
from utils.config import get_project_root

# Define the relative paths to create under the project root
DATA_DIRS = [
    "data/raw/human_samples",
    "data/raw/llm_samples",
    "data/raw/reference_set",
    "data/intermediate",
    "data/processed",
    "figures",
]

def setup_data_directories():
    """
    Creates all necessary data directories if they do not already exist.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    success = True

    logger.info(f"Project root identified at: {project_root}")

    for dir_path_str in DATA_DIRS:
        full_path = project_root / dir_path_str
        
        if full_path.exists():
            logger.info(f"Directory already exists: {full_path}")
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                success = False

    if success:
        logger.info("All data directories successfully verified/created.")
    else:
        logger.error("Some directories failed to create.")
        
    return success

def main():
    """Entry point for the script."""
    logger = get_logger(__name__)
    logger.info("Starting data directory setup...")
    
    if setup_data_directories():
        logger.info("Setup completed successfully.")
        return 0
    else:
        logger.error("Setup failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())