"""
Script to create the full project directory tree for PROJ-191.
This implements T001 by executing the required mkdir -p command structure.
"""
import os
import sys
from pathlib import Path
import logging
from config import get_logger, setup_logging

def main():
    """Create the project directory structure."""
    # Ensure logging is set up first
    setup_logging()
    logger = get_logger(__name__)

    # Define the project root relative to the current working directory
    # The task specifies the path relative to the repository root.
    # We assume the script is run from the repository root or the project root.
    project_root = Path("projects/PROJ-191-investigating-the-validity-of-the-invers")

    # Define the directory structure components
    # Using a set of paths to ensure all required subdirectories are created
    directories = [
        "code",
        "tests",
        "data",
        "docs",
        "code/data",
        "code/models",
        "code/inference",
        "code/robustness",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]

    logger.info(f"Creating project directory tree at: {project_root}")

    created_count = 0
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
                logger.debug(f"Created directory: {full_path}")
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                return 1
        else:
            logger.debug(f"Directory already exists: {full_path}")

    logger.info(f"Successfully created {created_count} new directories.")
    
    # Verify the structure by listing the root
    if project_root.exists():
        logger.info(f"Verification: Project root {project_root} exists.")
        # List immediate subdirectories to confirm
        subdirs = [d.name for d in project_root.iterdir() if d.is_dir()]
        logger.info(f"Subdirectories found: {subdirs}")
    else:
        logger.error("Verification failed: Project root does not exist.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())