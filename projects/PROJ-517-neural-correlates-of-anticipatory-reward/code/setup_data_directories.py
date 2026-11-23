"""
Task T001c: Create data directories.

Creates the following directories relative to the project root:
- data/raw/
- data/processed/
- data/figures/

Verifies existence after creation.
"""
import os
from pathlib import Path
import logging
from logging_config import setup_logging, get_logger

# Configure logging
setup_logging()
logger = get_logger(__name__)

# Define the data directories to create
DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/figures"
]

def create_directory(dir_path: str) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        dir_path: Relative path to the directory.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    path = Path(dir_path)
    
    if path.exists():
        logger.info(f"Directory already exists: {path}")
        return True
    
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {path}")
        
        # Verify creation
        if path.exists() and path.is_dir():
            return True
        else:
            logger.error(f"Directory creation verification failed: {path}")
            return False
    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        return False

def main():
    """Main entry point for T001c."""
    logger.info("Starting T001c: Create data directories")
    
    all_success = True
    for dir_path in DATA_DIRS:
        if not create_directory(dir_path):
            all_success = False
    
    if all_success:
        logger.info("T001c completed successfully. All data directories created and verified.")
    else:
        logger.error("T001c failed. Some directories could not be created.")
        # Exit with non-zero code to indicate failure
        import sys
        sys.exit(1)

if __name__ == "__main__":
    main()
