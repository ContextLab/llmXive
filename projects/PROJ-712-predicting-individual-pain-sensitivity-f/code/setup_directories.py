"""
Module to initialize project directory structure.
Implements Task T001: Create data/raw/, data/processed/, artifacts/, state/, code/, and tests/ directories.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories(root_dir: Optional[Path] = None) -> list:
    """
    Creates the required project directory structure relative to root_dir.
    If root_dir is None, uses the current working directory.
    
    Args:
        root_dir: Optional base path for the project. Defaults to cwd.
        
    Returns:
        List of created Path objects.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    # Define required directories relative to root
    required_dirs = [
        "data/raw",
        "data/processed",
        "artifacts",
        "state",
        "code",
        "tests"
    ]
    
    created_paths = []
    
    for dir_name in required_dirs:
        full_path = root_dir / dir_name
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_paths.append(full_path)
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise e
    
    return created_paths

def validate_paths(root_dir: Optional[Path] = None) -> bool:
    """
    Validates that all required directories exist.
    
    Args:
        root_dir: Optional base path for the project. Defaults to cwd.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "artifacts",
        "state",
        "code",
        "tests"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        full_path = root_dir / dir_name
        if not full_path.is_dir():
            logger.error(f"Missing required directory: {full_path}")
            all_exist = False
        else:
            logger.debug(f"Directory exists: {full_path}")
    
    return all_exist

def main():
    """
    Main entry point to initialize the project structure.
    """
    logger.info("Initializing project directory structure...")
    
    # Use current working directory as root
    root_dir = Path.cwd()
    logger.info(f"Using root directory: {root_dir}")
    
    try:
        created = ensure_directories(root_dir)
        logger.info(f"Successfully created {len(created)} directories.")
        
        if validate_paths(root_dir):
            logger.info("Validation passed: All required directories exist.")
            return 0
        else:
            logger.error("Validation failed: Some directories are missing.")
            return 1
    except Exception as e:
        logger.error(f"Error during directory initialization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
