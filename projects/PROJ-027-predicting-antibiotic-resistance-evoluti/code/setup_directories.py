import os
import sys
from pathlib import Path
from utils.logging import get_logger

# Define the directory structure to be created
DIRECTORIES = [
    "code/01_ingest",
    "code/02_process",
    "code/03_model",
    "code/04_validate",
    "code/05_viz",
]

def create_directories(logger):
    """
    Creates the required directory structure for the project.
    
    Args:
        logger: Logger instance for logging operations.
    """
    for dir_path in DIRECTORIES:
        path = Path(dir_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created or verified: {path}")
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

def verify_directories(logger):
    """
    Verifies that all required directories exist.
    
    Args:
        logger: Logger instance for logging operations.
    
    Returns:
        bool: True if all directories exist, False otherwise.
    """
    all_exist = True
    for dir_path in DIRECTORIES:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            logger.info(f"Verified: {path} exists")
        else:
            logger.error(f"Verification failed: {path} does not exist")
            all_exist = False
    return all_exist

def main():
    """
    Main entry point for the directory setup script.
    """
    logger = get_logger("setup_directories")
    logger.info("Starting directory creation and verification...")
    
    create_directories(logger)
    
    if verify_directories(logger):
        logger.info("All required directories are present.")
        sys.exit(0)
    else:
        logger.error("Some directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()