"""
Project Setup Script for PROJ-436.

This script initializes the required directory structure and creates
necessary __init__.py files to ensure the project is ready for development
and execution.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories(base_path: Path):
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: The root path where directories should be created.
    """
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "specs",
        "contracts",
        "figures"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    logger.info(f"Directory setup complete. {created_count} new directories created.")

def create_init_files(base_path: Path):
    """
    Create __init__.py files in all Python package directories.
    
    Args:
        base_path: The root path of the project.
    """
    python_dirs = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    for dir_name in python_dirs:
        dir_path = base_path / dir_name
        init_file = dir_path / "__init__.py"
        
        if not init_file.exists():
          # Create an empty __init__.py to mark it as a package
          init_file.touch()
          logger.info(f"Created __init__.py in {dir_path}")
        else:
          logger.debug(f"__init__.py already exists in {dir_path}")

def main():
    """Main entry point for the setup script."""
    # Determine the project root. 
    # We assume the script is run from the project root or the code directory.
    # If run from code/, we go up one level.
    current_file = Path(__file__).resolve()
    if current_file.name == "setup_project.py":
        # Check if we are in a 'code' subdirectory
        if current_file.parent.name == "code":
            project_root = current_file.parent.parent
        else:
            project_root = current_file.parent
    else:
        project_root = Path.cwd()

    logger.info(f"Project root identified as: {project_root}")

    # Create directories
    create_directories(project_root)

    # Create __init__.py files
    create_init_files(project_root)

    logger.info("Project structure setup completed successfully.")

if __name__ == "__main__":
    main()
