import os
import sys
from pathlib import Path
import logging
from utils.logging_config import get_logger

def ensure_directory(path: str) -> bool:
    """
    Ensure the specified directory exists. Creates it if it doesn't.
    
    Args:
        path: The directory path to ensure exists (relative to project root)
        
    Returns:
        bool: True if directory exists or was created successfully, False otherwise
    """
    try:
        full_path = Path(path)
        full_path.mkdir(parents=True, exist_ok=True)
        logger = get_logger()
        logger.info(f"Ensured directory exists: {full_path.resolve()}")
        return True
    except Exception as e:
        logger = get_logger()
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def main():
    """
    Main entry point for creating data directories.
    Creates data/raw/ and data/processed/ directories.
    """
    logger = get_logger()
    logger.info("Starting data directory setup...")
    
    # Define the directories to create
    data_dirs = [
        "data/raw",
        "data/processed"
    ]
    
    success = True
    for dir_path in data_dirs:
        if not ensure_directory(dir_path):
            success = False
    
    if success:
        logger.info("Data directories created successfully.")
        print("Data directories created successfully.")
    else:
        logger.error("Failed to create some data directories.")
        print("Failed to create some data directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()
