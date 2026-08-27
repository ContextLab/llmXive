"""
Setup script to create the full project directory tree.
This script ensures all required directories exist for the project structure.
"""
import os
import sys
from pathlib import Path
import logging
from config import get_logger, setup_logging

def main():
    """
    Create the full project directory tree at the repository root.
    Uses mkdir -p logic to ensure all subdirectories are created atomically.
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    # Define the project root relative to the code directory
    # The code directory is at projects/PROJ-191-investigating-the-validity-of-the-invers/code/
    # So we go up two levels to reach the project root
    current_path = Path(__file__).resolve()
    code_dir = current_path.parent
    project_root = code_dir.parent

    logger.info(f"Project root detected at: {project_root}")

    # Define the directory structure to create
    # Based on the task description:
    # code/, tests/, data/, docs/
    # code/data/, code/models/, code/inference/, code/robustness/, code/utils/
    # data/raw/, data/processed/, data/results/
    # tests/unit/, tests/contract/, tests/integration/
    
    directories_to_create = [
        "code",
        "code/data",
        "code/models",
        "code/inference",
        "code/robustness",
        "code/utils",
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories_to_create:
        full_path = project_root / dir_path
        
        if full_path.exists():
            logger.debug(f"Directory already exists: {full_path}")
            existing_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1

    logger.info(f"Directory setup complete. Created {created_count} new directories, "
               f"{existing_count} already existed.")
    
    # Verify the structure
    logger.info("Verifying directory structure...")
    missing = []
    for dir_path in directories_to_create:
        full_path = project_root / dir_path
        if not full_path.exists() or not full_path.is_dir():
            missing.append(str(full_path))
    
    if missing:
        logger.error(f"Verification failed. Missing directories: {missing}")
        return 1
    
    logger.info("All required directories verified successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())