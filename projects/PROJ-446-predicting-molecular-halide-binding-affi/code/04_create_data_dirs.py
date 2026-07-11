import os
from pathlib import Path
from code.utils.logger import get_logger

def create_directories():
    """
    Creates the required directory structure for the project:
    - data/raw/
    - data/processed/
    - data/simulated/
    - docs/paper/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    logger = get_logger(__name__)
    
    # Define the project root relative to this script's location
    # Assuming this script is in code/ and we need to go up one level to project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # Define the directories to create relative to project root
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "simulated",
        project_root / "docs" / "paper",
    ]
    
    success = True
    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False
    
    return success

def main():
    """Entry point for the directory creation script."""
    logger = get_logger(__name__)
    logger.info("Starting directory creation for T004...")
    
    success = create_directories()
    
    if success:
        logger.info("All directories created successfully.")
    else:
        logger.error("Some directories failed to be created.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())