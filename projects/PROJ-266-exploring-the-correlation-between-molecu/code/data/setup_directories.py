import logging
import sys
from pathlib import Path
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

def create_directories():
    """
    Create and verify directory structure for:
    - data/raw/
    - data/processed/
    - state/projects/
    - state/pending/
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    dirs_to_create = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
        project_root / 'state' / 'projects',
        project_root / 'state' / 'pending',
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")
    
    return True

def verify_directories():
    """
    Verify that all required directories exist.
    Raises AssertionError if any directory is missing.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    required_dirs = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
        project_root / 'state' / 'projects',
        project_root / 'state' / 'pending',
    ]
    
    for dir_path in required_dirs:
        assert dir_path.is_dir(), f"Directory does not exist: {dir_path}"
        logger.info(f"Verified directory: {dir_path}")
    
    return True

def main():
    """
    Main entry point for directory setup and verification.
    """
    configure_root_logger()
    logger = get_logger(__name__)
    logger.info("Starting directory setup and verification...")
    
    create_directories()
    verify_directories()
    
    logger.info("Directory setup and verification completed successfully.")
    return True

if __name__ == '__main__':
    main()