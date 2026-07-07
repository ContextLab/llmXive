"""
Directory setup module for the Exoplanetary Atmospheres Characterization project.

This module handles the creation and verification of required directory structures
for code organization, testing, and data storage.
"""
import os
import sys
from pathlib import Path
import logging
from utils import setup_logging

# Define the required directory structure relative to the project root
REQUIRED_DIRS = [
    "code",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "data/raw",
    "data/processed",
    "results/plots",
    "figures",
]

def create_directories(base_path: Path = None) -> dict:
    """
    Create all required directories if they do not exist.

    Args:
        base_path: The project root directory. Defaults to the directory
                   containing this script's parent (project root).

    Returns:
        dict: A dictionary mapping directory paths to their creation status
              {'created': bool, 'exists': bool}.
    """
    if base_path is None:
        # Assume project root is the parent of the 'code' directory
        # or the current working directory if running from root
        base_path = Path.cwd()

    results = {}
    logger = logging.getLogger(__name__)

    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        created = False
        exists = full_path.exists()

        if not exists:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created = True
                logger.info(f"Created directory: {full_path}")
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                results[dir_name] = {"created": False, "exists": False, "error": str(e)}
                continue
        else:
            logger.debug(f"Directory already exists: {full_path}")

        results[dir_name] = {"created": created, "exists": True}

    return results

def verify_directories(base_path: Path = None) -> bool:
    """
    Verify that all required directories exist.

    Args:
        base_path: The project root directory.

    Returns:
        bool: True if all directories exist, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()

    logger = logging.getLogger(__name__)
    all_exist = True

    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        if not full_path.exists():
            logger.error(f"Missing required directory: {full_path}")
            all_exist = False
        elif not full_path.is_dir():
            logger.error(f"Path exists but is not a directory: {full_path}")
            all_exist = False

    if all_exist:
        logger.info("All required directories verified successfully.")
    else:
        logger.warning("Some required directories are missing or invalid.")

    return all_exist

def main():
    """
    Main entry point for directory setup script.
    Creates directories and verifies their existence.
    """
    # Setup logging
    log_path = Path("results") / "setup_logs"
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / "directory_setup.log"

    logger = setup_logging(log_file=log_file, level=logging.INFO)
    logger.info("Starting directory setup for PROJ-554...")

    base_path = Path.cwd()
    logger.info(f"Project root identified as: {base_path}")

    # Create directories
    creation_results = create_directories(base_path)

    # Verify directories
    is_valid = verify_directories(base_path)

    if is_valid:
        logger.info("Directory setup completed successfully.")
        return 0
    else:
        logger.error("Directory setup failed verification.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
