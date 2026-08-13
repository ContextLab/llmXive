"""
Module to setup the required directory structure for the project.
Creates data/raw, data/processed, and data/artifacts directories.
"""
import os
from pathlib import Path
import logging

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories():
    """
    Creates the required directory structure for the project data.
    Specifically creates:
    - data/raw/
    - data/processed/
    - data/artifacts/
    
    Returns:
        bool: True if all directories were created or already exist, False otherwise.
    """
    # Define the project root (assuming this script is in code/, project root is parent)
    # However, to be safe and consistent with the project structure, we assume
    # the script is run from the project root or the paths are relative to the current working directory.
    # The task requires paths relative to project root under data/
    
    base_path = Path("data")
    
    directories = [
        base_path / "raw",
        base_path / "processed",
        base_path / "artifacts"
    ]
    
    success = True
    
    for dir_path in directories:
        try:
            # create parents=True to ensure the full path exists
            # exist_ok=True prevents errors if directory already exists
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created or confirmed: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False
    
    if success:
        logger.info("All required data directories are ready.")
    else:
        logger.error("Some directories failed to create.")
        
    return success

if __name__ == "__main__":
    logger.info("Starting directory setup...")
    setup_directories()
    logger.info("Directory setup complete.")