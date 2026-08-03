"""
Directory Structure Initialization Module.

This module implements Task T001a: Initialize Project Directory Structure.
It creates the required directory tree for the llmXive project, ensuring
that all necessary folders for code, data, tests, and simulations exist.

The structure aligns with the project plan:
- code/: Source code modules
  - data_generation/
  - model_training/
  - simulation/
  - analysis/
- data/: Data artifacts
  - raw/
  - processed/
  - models/
  - simulation/
- tests/: Unit and integration tests
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the directory structure relative to the project root
# Based on tasks.md: T001a
DIRECTORIES_TO_CREATE = [
    # Code modules
    "code/data_generation",
    "code/model_training",
    "code/simulation",
    "code/analysis",
    
    # Data directories
    "data/raw",
    "data/processed",
    "data/models",
    "data/simulation",
    
    # Tests
    "tests",
]

def get_project_root() -> Path:
    """
    Determine the project root directory.
    
    Assumes the script is run from the project root or that 'code' 
    is a direct subdirectory of the root.
    
    Returns:
        Path: The absolute path to the project root.
    """
    # Try to find the directory containing this file
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    
    # If this file is in code/, the root is the parent
    if code_dir.name == "code":
        return code_dir.parent
    
    # Fallback: assume current working directory is root
    # This handles cases where the script is run via python code/setup_directories.py
    # but the cwd is not set correctly in some environments
    return Path.cwd()

def create_directories(root_dir: Path, dir_list: list) -> None:
    """
    Create all specified directories under the root directory.
    
    Args:
        root_dir: The base directory path.
        dir_list: List of relative directory paths to create.
        
    Raises:
        OSError: If a directory cannot be created.
    """
    for dir_path in dir_list:
        full_path = root_dir / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise

def verify_structure(root_dir: Path, dir_list: list) -> bool:
    """
    Verify that all required directories exist.
    
    Args:
        root_dir: The base directory path.
        dir_list: List of relative directory paths to check.
        
    Returns:
        bool: True if all directories exist, False otherwise.
    """
    all_exist = True
    for dir_path in dir_list:
        full_path = root_dir / dir_path
        if not full_path.is_dir():
            logger.error(f"Directory missing: {full_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {full_path}")
    
    return all_exist

def main() -> int:
    """
    Main entry point for the directory initialization script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting project directory initialization...")
    
    try:
        root = get_project_root()
        logger.info(f"Project root detected at: {root}")
        
        # Create directories
        create_directories(root, DIRECTORIES_TO_CREATE)
        
        # Verify creation
        if verify_structure(root, DIRECTORIES_TO_CREATE):
            logger.info("Directory structure initialization completed successfully.")
            return 0
        else:
            logger.error("Directory structure verification failed.")
            return 1
            
    except Exception as e:
        logger.exception(f"Unexpected error during initialization: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
