"""
create_results_dirs.py

Implements the creation of the results directory structure required for the project.
Specifically creates 'results/figures/' as per task T009.
"""
import os
import sys
import logging

# Import utilities from the existing code base
from utils import get_logger, set_task_id, get_task_id


def ensure_results_directories():
    """
    Creates the required results directory structure.
    Specifically ensures 'results/figures/' exists.

    Returns:
        bool: True if successful, False otherwise.
    """
    logger = get_logger()
    task_id = get_task_id()
    set_task_id(task_id)  # Ensure context is set

    # Define the base results directory
    base_dir = "results"
    figures_dir = os.path.join(base_dir, "figures")

    directories_to_create = [base_dir, figures_dir]

    success = True
    for dir_path in directories_to_create:
        if not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            except OSError as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                success = False
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    return success


def main():
    """
    Main entry point for the script.
    Sets up logging, executes directory creation, and returns appropriate exit code.
    """
    # Initialize task ID for logging if not already set
    task_id = get_task_id()
    if not task_id:
        set_task_id("T009")

    logger = setup_logging()
    logger.info(f"Starting task {get_task_id()}: Creating results directory structure")

    success = ensure_results_directories()

    if success:
        logger.info(f"Task {get_task_id()} completed successfully. 'results/figures/' is ready.")
        sys.exit(0)
    else:
        logger.error(f"Task {get_task_id()} failed. Some directories could not be created.")
        sys.exit(1)


if __name__ == "__main__":
    main()
