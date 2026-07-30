import os
import sys
from pathlib import Path
from typing import List, Optional
from utils import get_logger

def create_directories(base_path: Optional[Path] = None) -> List[Path]:
    """
    Creates the required project directory structure.
    
    Args:
        base_path: Optional base path. Defaults to current working directory.
        
    Returns:
        List of created Path objects.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define the required directories relative to the base path
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    created_paths = []
    logger = get_logger("setup_project")
    
    for dir_name in directories:
        full_path = base_path / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(full_path)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    return created_paths

def verify_directories(base_path: Optional[Path] = None) -> bool:
    """
    Verifies that all required directories exist.
    
    Args:
        base_path: Optional base path. Defaults to current working directory.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    logger = get_logger("setup_project")
    all_exist = True
    
    for dir_name in required_dirs:
        full_path = base_path / dir_name
        if not full_path.is_dir():
            logger.warning(f"Missing directory: {full_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {full_path}")
    
    return all_exist

def main():
    """Main entry point for project setup."""
    logger = get_logger("setup_project")
    logger.info("Starting project directory setup...")
    
    try:
        created = create_directories()
        logger.info(f"Successfully created {len(created)} directories.")
        
        if verify_directories():
            logger.info("Verification successful: All required directories exist.")
            return 0
        else:
            logger.error("Verification failed: Some directories are missing.")
            return 1
    except Exception as e:
        logger.exception(f"Setup failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
