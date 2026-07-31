import os
import sys
from pathlib import Path
from typing import List, Optional
from utils import get_logger

def create_directories(root_dir: Optional[Path] = None) -> List[Path]:
    """
    Create the required project directory structure.
    
    Returns a list of created paths for verification.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    # Define the required directory structure relative to root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    created_paths = []
    logger = get_logger(__name__)
    
    for dir_str in directories:
        full_path = root_dir / dir_str
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(full_path)
            logger.info(f"Created directory: {full_path}")
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    return created_paths

def verify_directories(root_dir: Optional[Path] = None) -> bool:
    """
    Verify that all required directories exist.
    
    Returns True if all directories exist, False otherwise.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    all_exist = True
    logger = get_logger(__name__)
    
    for dir_str in required_dirs:
        full_path = root_dir / dir_str
        if not full_path.exists() or not full_path.is_dir():
            logger.error(f"Missing required directory: {full_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {full_path}")
    
    return all_exist

def main():
    """Main entry point for project setup."""
    logger = get_logger(__name__)
    logger.info("Starting project directory setup...")
    
    root = Path.cwd()
    created = create_directories(root)
    
    if created:
        logger.info(f"Successfully created {len(created)} new directories.")
    else:
        logger.info("All required directories already exist.")
    
    if verify_directories(root):
        logger.info("Project directory structure verification: PASSED")
        return 0
    else:
        logger.error("Project directory structure verification: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())