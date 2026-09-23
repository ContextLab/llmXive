"""
Task T008a: Create and verify directory structure for data and state directories.

This script creates the required directory structure for the project:
- data/raw/
- data/processed/
- state/projects/
- state/pending/

It also verifies that the directories were created successfully.
"""
import logging
import sys
from pathlib import Path
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

def create_directories():
    """
    Create the required directory structure for the project.
    
    Returns:
        Path: The project root path.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    # Define the directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects",
        project_root / "state" / "pending",
    ]
    
    logger.info("Creating directory structure...")
    
    for directory in directories:
        logger.info(f"Creating directory: {directory}")
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Successfully created directory: {directory}")
    
    return project_root

def verify_directories(project_root: Path):
    """
    Verify that the required directories exist.
    
    Args:
        project_root: The project root path.
        
    Raises:
        AssertionError: If any required directory does not exist.
    """
    logger = get_logger(__name__)
    
    # Define the directories to verify
    directories = {
        "data/raw": project_root / "data" / "raw",
        "data/processed": project_root / "data" / "processed",
        "state/projects": project_root / "state" / "projects",
        "state/pending": project_root / "state" / "pending",
    }
    
    logger.info("Verifying directory structure...")
    
    for name, directory in directories.items():
        logger.info(f"Verifying directory: {name}")
        assert directory.is_dir(), f"Directory {name} does not exist: {directory}"
        logger.info(f"Successfully verified directory: {name}")
    
    logger.info("All directories verified successfully.")

def main():
    """Main entry point for the script."""
    configure_root_logger()
    logger = get_logger(__name__)
    
    try:
        # Create directories
        project_root = create_directories()
        
        # Verify directories
        verify_directories(project_root)
        
        logger.info("Task T008a completed successfully.")
        return 0
    except AssertionError as e:
        logger.error(f"Verification failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
