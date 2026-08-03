import os
import sys
from pathlib import Path
from typing import List, Optional
from utils import get_logger, get_project_paths

def create_directories(root_dir: Optional[Path] = None) -> List[Path]:
    """
    Create the required project directory structure.
    
    Returns a list of created directory paths.
    """
    logger = get_logger("setup_project")
    if root_dir is None:
        root_dir = get_project_paths().root
    
    # Define the required directory structure relative to root
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    created_paths = []
    
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_paths.append(full_path)
        else:
            logger.debug(f"Directory already exists: {full_path}")
            
    return created_paths

def verify_directories(root_dir: Optional[Path] = None) -> bool:
    """
    Verify that all required directories exist.
    
    Returns True if all directories exist, False otherwise.
    """
    logger = get_logger("setup_project")
    if root_dir is None:
        root_dir = get_project_paths().root
        
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        if not full_path.exists() or not full_path.is_dir():
            logger.error(f"Missing required directory: {full_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {full_path}")
            
    return all_exist

def main():
    """
    Main entry point for project setup.
    Creates directory structure and verifies existence.
    """
    logger = get_logger("setup_project")
    logger.info("Starting project directory setup...")
    
    # Create directories
    created = create_directories()
    
    if not created:
        logger.info("No new directories were created (all already exist).")
    else:
        logger.info(f"Successfully created {len(created)} directories.")
        
    # Verify
    if verify_directories():
        logger.info("Project directory structure verification: PASSED")
        return 0
    else:
        logger.error("Project directory structure verification: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
