import os
import sys
from pathlib import Path

from utils.config import get_project_root, ensure_dir
from utils.logging import get_logger

logger = get_logger(__name__)

def create_directories():
    """
    Creates the required directory structure for the project:
    - code/
    - data/raw
    - data/interim
    - data/processed
    - tests/unit
    - tests/integration
    - state/projects/PROJ-922
    """
    root = get_project_root()
    logger.info(f"Creating directory structure under project root: {root}")

    # Define relative paths to create
    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state/projects/PROJ-922"
    ]

    created_count = 0
    for rel_path in directories:
        full_path = root / rel_path
        if ensure_dir(full_path):
            created_count += 1
            logger.info(f"Created directory: {full_path}")
        else:
            logger.debug(f"Directory already exists: {full_path}")

    logger.info(f"Directory creation complete. {created_count} new directories created.")
    return True

def main():
    """Entry point for script execution."""
    try:
        success = create_directories()
        if success:
            print("Directory structure setup successful.")
            sys.exit(0)
        else:
            print("Directory structure setup failed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during directory creation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()