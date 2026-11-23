import os
import sys
from pathlib import Path
from utils.logging import get_logger

# Define the directory structure relative to the project root
# Based on T001b and T007 requirements
DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/models",
]

def create_data_directories():
    """
    Creates the required data directory structure.
    Returns a list of created directory paths.
    """
    logger = get_logger("setup_data_dirs")
    created_dirs = []
    project_root = Path(__file__).resolve().parent.parent

    for dir_path in DATA_DIRS:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_dirs.append(full_path)
        else:
            logger.debug(f"Directory already exists: {full_path}")

    return created_dirs

def verify_data_directories():
    """
    Verifies that all required data directories exist.
    Returns True if all exist, False otherwise.
    """
    logger = get_logger("setup_data_dirs")
    project_root = Path(__file__).resolve().parent.parent
    all_exist = True

    for dir_path in DATA_DIRS:
        full_path = project_root / dir_path
        if not full_path.is_dir():
            logger.error(f"Missing directory: {full_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {full_path}")

    return all_exist

def main():
    """
    Main entry point for setting up data directories.
    """
    logger = get_logger("setup_data_dirs")
    logger.info("Starting data directory setup...")

    created = create_data_directories()
    if created:
        logger.info(f"Successfully created {len(created)} directories.")
    else:
        logger.info("No new directories created (all already exist).")

    if verify_data_directories():
        logger.info("Verification passed: All required directories exist.")
        return 0
    else:
        logger.error("Verification failed: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
