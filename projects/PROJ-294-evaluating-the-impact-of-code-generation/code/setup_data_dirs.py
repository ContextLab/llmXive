import os
import sys
import logging
from utils import get_logger, set_task_id, get_task_id

def create_directories():
    """
    Creates the required data directory structure for the project.
    Implements Task T008.
    """
    # Define the project root based on the current file location
    # The script is in code/, so project root is parent of code/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    data_root = os.path.join(project_root, "data")
    
    # Define the specific directories required by T008
    directories = [
        os.path.join(data_root, "raw"),
        os.path.join(data_root, "generated"),
        os.path.join(data_root, "analysis")
    ]
    
    # Ensure the main data root exists
    os.makedirs(data_root, exist_ok=True)
    
    created_count = 0
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            created_count += 1
            # Log only if we are in the main execution context
            # Avoid spamming logs if imported multiple times
            if "main" in sys.argv[0]:
                logger = get_logger()
                if logger:
                    logger.info(f"Created directory: {directory}")
        except OSError as e:
            logger = get_logger()
            if logger:
                logger.error(f"Failed to create directory {directory}: {e}")
            raise

    return created_count

def main():
    """Entry point for T008 execution."""
    set_task_id("T008")
    logger = get_logger()
    if logger:
        logger.info("Starting T008: Create data directory structure")
    
    try:
        count = create_directories()
        if logger:
            logger.info(f"T008 completed successfully. Created {count} directories.")
        return 0
    except Exception as e:
        if logger:
            logger.error(f"T008 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
