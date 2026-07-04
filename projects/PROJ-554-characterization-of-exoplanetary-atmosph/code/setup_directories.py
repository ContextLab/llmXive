import os
import sys
from pathlib import Path
import logging
from utils import setup_logging

def create_directories():
    """
    Create code and test directory structure for the project.
    Verifies existence of all required directories.
    
    Returns:
        bool: True if all directories were created/verified successfully, False otherwise.
    """
    logger = logging.getLogger(__name__)
    
    # Define the directories to create relative to the project root
    # Assuming the script runs from the project root or code/ directory
    # We use the parent of this file's directory to find the project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    directories = [
        project_root / "code",
        project_root / "tests" / "unit",
        project_root / "tests" / "contract",
        project_root / "tests" / "integration",
    ]
    
    success = True
    
    for dir_path in directories:
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            else:
                logger.info(f"Directory already exists: {dir_path}")
                
            # Verify it's actually a directory
            if not dir_path.is_dir():
                logger.error(f"Path exists but is not a directory: {dir_path}")
                success = False
                
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False
    
    return success

def main():
    """Main entry point for directory setup."""
    # Setup logging
    logger = setup_logging("setup_directories")
    
    logger.info("Starting directory creation and verification...")
    
    if create_directories():
        logger.info("All directories created and verified successfully.")
        sys.exit(0)
    else:
        logger.error("Directory creation failed for one or more paths.")
        sys.exit(1)

if __name__ == "__main__":
    main()