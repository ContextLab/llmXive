"""
Script to initialize the data directory structure for the llmXive project.

Creates the following directories under the project root:
- data/raw: For raw input datasets and generated synthetic data
- data/processed: For cleaned and transformed data
- data/results: For final simulation outputs and analysis results
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Determine the project root directory.
    
    Assumes the script is located at code/setup_data_directories.py
    and the project root is the parent of the code directory.
    
    Returns:
        Path: The absolute path to the project root.
    """
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    return project_root

def create_directories(project_root: Path) -> bool:
    """
    Create the required data directory structure.
    
    Args:
        project_root (Path): The root directory of the project.
        
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    data_dir = project_root / "data"
    directories = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "results"
    ]
    
    success = True
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            success = False
    
    return success

def verify_structure(project_root: Path) -> bool:
    """
    Verify that the required data directories exist.
    
    Args:
        project_root (Path): The root directory of the project.
        
    Returns:
        bool: True if all required directories exist, False otherwise.
    """
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if not directory.is_dir():
            logger.error(f"Missing directory: {directory}")
            all_exist = False
        else:
            logger.info(f"Verified directory exists: {directory}")
    
    return all_exist

def main():
    """
    Main entry point for the data directory initialization script.
    """
    logger.info("Starting data directory initialization...")
    
    try:
        project_root = get_project_root()
        logger.info(f"Project root detected at: {project_root}")
        
        if create_directories(project_root):
            logger.info("All directories created successfully.")
            if verify_structure(project_root):
                logger.info("Directory structure verification passed.")
                return 0
            else:
                logger.error("Directory structure verification failed.")
                return 1
        else:
            logger.error("Failed to create one or more directories.")
            return 1
            
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())