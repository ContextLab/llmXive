"""
Project Directory Structure Setup Script.

This script initializes the root directory structure required for the llmXive
automated science pipeline. It creates the `code/`, `data/`, `tests/`, and
`state/` directories along with their standard subdirectories as defined in
the project plan.

Execution:
    python code/setup_directory_structure.py

Verification:
    ls code/
    ls data/
    ls tests/
    ls state/
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Define the root directory (project root)
# Assuming this script runs from the project root or code/ subdirectory
# We resolve the project root as the parent of 'code' if we are inside 'code',
# otherwise the current working directory.
def get_project_root():
    current = Path.cwd()
    if current.name == "code":
        return current.parent
    return current

def create_directories():
    """
    Creates the standard project directory structure.
    """
    root = get_project_root()
    logger.info(f"Project root detected at: {root}")

    # Define directory structure relative to root
    # Phase 1: Setup (Shared Infrastructure)
    code_dirs = [
        "code/data_generation",
        "code/model_training",
        "code/simulation",
        "code/analysis",
        "code/utils",
    ]

    data_dirs = [
        "data/raw",
        "data/processed",
        "data/models",
        "data/simulation",
        "data/generated", # Added for T017a output
        "data/metrics",   # Added for T023/T035c output
        "data/analysis",  # Added for T025/T032 output
    ]

    tests_dirs = [
        "tests/test_data_generation",
        "tests/test_model_training",
        "tests/test_simulation",
        "tests/test_analysis",
    ]

    state_dirs = [
        "state", # For checksums and run states
    ]

    all_dirs = code_dirs + data_dirs + tests_dirs + state_dirs

    created_count = 0
    for dir_path in all_dirs:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")

    logger.info(f"Directory setup complete. Created {created_count} new directories.")
    return True

def verify_structure():
    """
    Verifies that the essential directories exist.
    """
    root = get_project_root()
    essential = [
        "code",
        "data",
        "tests",
        "state",
    ]

    missing = []
    for dir_name in essential:
        if not (root / dir_name).exists():
            missing.append(dir_name)

    if missing:
        logger.error(f"Verification failed. Missing directories: {missing}")
        return False

    logger.info("Verification passed. All essential directories exist.")
    return True

def main():
    """
    Entry point for the script.
    """
    try:
        if create_directories():
            if verify_structure():
                logger.info("Setup successful.")
                return 0
            else:
                logger.error("Setup created directories but verification failed.")
                return 1
        else:
            logger.error("Directory creation failed.")
            return 1
    except Exception as e:
        logger.exception(f"An error occurred during setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())