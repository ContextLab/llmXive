import os
import logging
from pathlib import Path
from config import get_project_root
from utils.logging import get_logger

logger = get_logger(__name__)

def create_directories() -> None:
    """
    Creates the required directory structure for the project.
    
    Directories created:
    - code/{data,stimuli,analysis,viz,tests}
    - data/{raw/stimuli,raw/responses,processed,results}
    - docs
    """
    project_root = get_project_root()
    
    # Define directory structure relative to project root
    directories = [
        # Code subdirectories
        project_root / "code" / "data",
        project_root / "code" / "stimuli",
        project_root / "code" / "analysis",
        project_root / "code" / "viz",
        project_root / "code" / "tests",
        
        # Data subdirectories
        project_root / "data" / "raw" / "stimuli",
        project_root / "data" / "raw" / "responses",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        
        # Documentation
        project_root / "docs",
    ]
    
    created_count = 0
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            logger.info(f"Created directory: {directory}")
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise
    
    logger.info(f"Successfully created {created_count} directories.")

def setup_directories() -> bool:
    """
    Wrapper function to setup directories and return success status.
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    try:
        create_directories()
        return True
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return False

def main() -> None:
    """Main entry point for directory setup."""
    logger.info("Starting directory setup...")
    success = setup_directories()
    if success:
        logger.info("Directory setup completed successfully.")
    else:
        logger.error("Directory setup failed.")
        raise RuntimeError("Directory setup failed.")
