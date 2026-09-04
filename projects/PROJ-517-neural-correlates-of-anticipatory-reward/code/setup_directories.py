"""
Directory setup module for PROJ-517-neural-correlates-of-anticipatory-reward.

Initializes all required project directories using os.makedirs with exist_ok=True.
This module is idempotent and can be run multiple times safely.
"""
import os
from pathlib import Path
import logging
from logging_config import setup_logging, get_logger

def create_directory(dir_path: Path, logger: logging.Logger) -> bool:
    """
    Create a directory if it does not exist.
    
    Uses os.makedirs with exist_ok=True to ensure idempotent behavior.
    
    Args:
        dir_path: Path object representing the directory to create
        logger: Logger instance for logging actions
        
    Returns:
        True if directory exists or was created successfully, False otherwise
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        if dir_path.exists() and dir_path.is_dir():
            logger.debug(f"Directory ready: {dir_path}")
            return True
        else:
            logger.error(f"Failed to create directory: {dir_path}")
            return False
    except OSError as e:
        logger.error(f"OS error creating directory {dir_path}: {e}")
        return False

def main():
    """
    Main entry point for directory setup script.
    
    Creates all required project directories and verifies their existence.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    project_root = Path.cwd()
    
    # Define required directories
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/figures",
    ]
    
    logger.info(f"Initializing directories in project root: {project_root}")
    
    success_count = 0
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if create_directory(dir_path, logger):
            success_count += 1
    
    logger.info(f"Directory initialization complete: {success_count}/{len(required_dirs)} directories ready.")
    
    # Verify all directories exist
    missing = [d for d in required_dirs if not (project_root / d).exists()]
    if missing:
        logger.error(f"Missing directories after initialization: {missing}")
        import sys
        sys.exit(1)
    else:
        logger.info("All required directories verified.")
        import sys
        sys.exit(0)

if __name__ == "__main__":
    main()