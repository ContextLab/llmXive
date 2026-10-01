import os
import sys
from pathlib import Path
from utils.logging import get_logger, configure_root_logger

def create_directories(logger):
    """
    Create the core project directories: code/, tests/, data/.
    Requirement: Execute os.makedirs('code/', exist_ok=True), etc.
    """
    dirs_to_create = ['code', 'tests', 'data']
    for dir_name in dirs_to_create:
        dir_path = Path(dir_name)
        logger.info(f"Creating directory: {dir_path}")
        os.makedirs(dir_path, exist_ok=True)
        if not dir_path.is_dir():
            raise RuntimeError(f"Failed to create directory: {dir_path}")
        logger.info(f"Successfully created or verified: {dir_path}")

def verify_directories(logger):
    """
    Verify that the required directories exist.
    """
    required_dirs = ['code', 'tests', 'data']
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if not dir_path.is_dir():
            raise FileNotFoundError(f"Required directory missing: {dir_path}")
        logger.info(f"Verified directory exists: {dir_path}")

def main():
    """
    Entry point for T002: Create project structure.
    """
    logger = configure_root_logger()
    logger.info("Starting T002: Create project structure")
    
    try:
        create_directories(logger)
        verify_directories(logger)
        logger.info("T002 completed successfully.")
    except Exception as e:
        logger.error(f"T002 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
