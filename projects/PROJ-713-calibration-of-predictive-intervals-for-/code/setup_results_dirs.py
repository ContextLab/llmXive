"""
Script to create and verify the results directory structure for the project.

This script ensures that the `results/`, `results/plots/`, and `results/tables/`
directories exist within the project root as defined in config.py.

Usage:
    python code/setup_results_dirs.py
"""
import os
from pathlib import Path
import sys
from config import PROJECT_ROOT, RESULTS_DIR, FIGURES_DIR
from utils.logger import get_logger

logger = get_logger(__name__)


def ensure_dir(dir_path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path object representing the directory to create.
        
    Returns:
        True if the directory exists or was successfully created, False otherwise.
    """
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")
        return True
    except PermissionError:
        logger.error(f"Permission denied when creating directory: {dir_path}")
        return False
    except OSError as e:
        logger.error(f"OS error when creating directory {dir_path}: {e}")
        return False


def main() -> int:
    """
    Main entry point for setting up results directories.
    
    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    logger.info("Starting results directory setup...")
    
    # Define the required directories
    dirs_to_create = [
        RESULTS_DIR,
        RESULTS_DIR / "plots",
        RESULTS_DIR / "tables",
        FIGURES_DIR,
    ]
    
    success = True
    for dir_path in dirs_to_create:
        if not ensure_dir(dir_path):
            success = False
    
    if success:
        logger.info("Results directory structure setup completed successfully.")
        return 0
    else:
        logger.error("Results directory structure setup failed due to errors.")
        return 1


if __name__ == "__main__":
    sys.exit(main())