import os
import sys
from pathlib import Path
import logging

def create_test_directories():
    """
    Create the required test and state directories for the project.
    
    Directories created:
    - tests/
    - state/projects/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    # Determine the project root (assuming this script is in code/ directory)
    project_root = Path(__file__).resolve().parent.parent
    
    directories_to_create = [
        project_root / "tests",
        project_root / "state" / "projects"
    ]
    
    success = True
    for directory in directories_to_create:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logging.info(f"Directory created or verified: {directory}")
        except OSError as e:
            logging.error(f"Failed to create directory {directory}: {e}")
            success = False
    
    return success

def main():
    """Main entry point for the test directory setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("Starting test directory creation...")
    
    if create_test_directories():
        logging.info("Test directories created successfully.")
        return 0
    else:
        logging.error("Failed to create one or more test directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
