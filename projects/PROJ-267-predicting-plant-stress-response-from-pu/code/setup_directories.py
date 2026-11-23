import os
import sys
from pathlib import Path
import logging
from utils.logging_config import get_logger

def ensure_directory(path_str: str) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path_str: Relative or absolute path to the directory.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    path = Path(path_str)
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger = get_logger(__name__)
        logger.info(f"Directory created/verified: {path.absolute()}")
        return True
    except OSError as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main entry point for T001a: Create project directories.
    Creates: code/, tests/, logs/, results/
    """
    logger = get_logger(__name__)
    logger.info("Starting directory setup for T001a...")
    
    # Define relative paths for the project root
    # Since this script runs from the project root or code/, we ensure
    # we are creating them relative to the current working directory
    # or explicitly relative to the project root if known.
    # Given the task description, these are relative to the project root.
    
    # We assume the script is run from the project root.
    # If run from 'code/', we need to adjust. 
    # Standard practice: run from root.
    
    directories = [
        "code",
        "tests",
        "logs",
        "results"
    ]
    
    success = True
    for dir_name in directories:
        if not ensure_directory(dir_name):
            success = False
    
    if success:
        logger.info("T001a: All required directories created successfully.")
        return 0
    else:
        logger.error("T001a: Failed to create one or more directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())