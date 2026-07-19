import os
import sys
import logging
from utils import get_logger, set_task_id, get_task_id

def create_directories():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/generated/
    - data/analysis/

    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    task_id = get_task_id()
    logger = get_logger()
    logger.info(f"[{task_id}] Starting directory creation for data structure.")

    # Define the base data directory relative to the project root
    # We assume the script is run from the project root or code/ directory
    # The paths must be relative to the project root as per constraints
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    directories = [
        os.path.join(base_dir, 'raw'),
        os.path.join(base_dir, 'generated'),
        os.path.join(base_dir, 'analysis')
    ]

    success = True
    for directory in directories:
        try:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"[{task_id}] Created directory: {directory}")
            else:
                logger.info(f"[{task_id}] Directory already exists: {directory}")
        except OSError as e:
            logger.error(f"[{task_id}] Failed to create directory {directory}: {e}")
            success = False

    if success:
        logger.info(f"[{task_id}] Data directory structure creation completed successfully.")
    else:
        logger.error(f"[{task_id}] Data directory structure creation failed.")

    return success

def main():
    """
    Entry point for the script.
    Sets up logging and executes directory creation.
    """
    set_task_id('T008')
    setup_logging()
    logger = get_logger()
    
    try:
        if create_directories():
            logger.info("Task T008 completed successfully.")
            sys.exit(0)
        else:
            logger.error("Task T008 failed due to directory creation errors.")
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error in T008: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
