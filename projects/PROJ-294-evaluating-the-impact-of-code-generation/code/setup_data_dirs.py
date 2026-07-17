"""
Setup script to create the required data directory structure for the project.
Creates: data/raw/, data/generated/, data/analysis/
"""
import os
import sys
from utils import get_logger, set_task_id, get_task_id

# Set task ID for logging
set_task_id("T008")
logger = get_logger()

# Define the required directories relative to the project root
# The project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")

DIRECTORIES_TO_CREATE = [
    "data/raw",
    "data/generated",
    "data/analysis"
]

def create_directories():
    """
    Creates the required data directories if they do not already exist.
    Logs success or failure for each directory.
    """
    logger.info(f"Starting directory creation for task {get_task_id()}")
    logger.info(f"Project root detected at: {PROJECT_ROOT}")
    
    created_count = 0
    skipped_count = 0

    for dir_path in DIRECTORIES_TO_CREATE:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        
        if os.path.exists(full_path):
            logger.info(f"Directory already exists: {full_path}")
            skipped_count += 1
        else:
            try:
                os.makedirs(full_path, exist_ok=True)
                logger.info(f"Successfully created directory: {full_path}")
                created_count += 1
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                return False

    logger.info(f"Directory setup complete. Created: {created_count}, Skipped: {skipped_count}")
    return True

def main():
    """
    Entry point for the script.
    Returns 0 on success, 1 on failure.
    """
    success = create_directories()
    if success:
        logger.info("Task T008 completed successfully.")
        return 0
    else:
        logger.error("Task T008 failed due to directory creation errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
