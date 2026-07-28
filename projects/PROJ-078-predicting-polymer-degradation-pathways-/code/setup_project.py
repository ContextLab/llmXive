"""
Project Directory Structure Setup Script.
Creates the required directory tree for the llmXive automated science pipeline.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional
from utils import get_logger

# Define the required directory structure relative to the project root
REQUIRED_DIRS: List[str] = [
    "code",
    "data/raw",
    "data/processed",
    "data/reports",
    "tests",
    "state",
]

def create_directories(base_path: Optional[Path] = None) -> List[Path]:
    """
    Create the required directory structure.
    
    Args:
        base_path: The root path for the project. Defaults to the current working directory.
        
    Returns:
        A list of created Path objects.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    created_dirs: List[Path] = []
    logger = get_logger(__name__)
    
    for dir_path_str in REQUIRED_DIRS:
        full_path = base_path / dir_path_str
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_dirs.append(full_path)
        else:
            logger.debug(f"Directory already exists: {full_path}")
            
    return created_dirs

def verify_directories(base_path: Optional[Path] = None) -> bool:
    """
    Verify that all required directories exist.
    
    Args:
        base_path: The root path for the project.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    logger = get_logger(__name__)
    all_exist = True
    
    for dir_path_str in REQUIRED_DIRS:
        full_path = base_path / dir_path_str
        if not full_path.is_dir():
            logger.error(f"Missing required directory: {full_path}")
            all_exist = False
            
    if all_exist:
        logger.info("All required directories verified.")
    else:
        logger.warning("Some required directories are missing.")
        
    return all_exist

def main():
    """Main entry point for the setup script."""
    logger = get_logger(__name__)
    logger.info("Starting project directory setup...")
    
    created = create_directories()
    if created:
        logger.info(f"Successfully created {len(created)} directories.")
    else:
        logger.info("No new directories created (all already exist).")
        
    if verify_directories():
        logger.info("Project structure setup complete.")
        return 0
    else:
        logger.error("Project structure setup failed verification.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
