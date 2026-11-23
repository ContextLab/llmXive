import os
import sys
from pathlib import Path
import logging

# Ensure the logger module is available if we need it, though for T001
# we just need to create directories.

def initialize_project_structure(root_dir: str = "projects/PROJ-064-statistical-discrepancies-in-publicly-av") -> bool:
    """
    Initialize the project directory structure for PROJ-064.
    
    Creates the following structure:
    root_dir/
    ├── code/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── tests/
    ├── docs/
    ├── state/
    └── config/
    
    Args:
        root_dir: The relative path to the project root directory.
        
    Returns:
        True if successful, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Initializing project structure at: {root_dir}")
    
    base_path = Path(root_dir)
    
    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "state",
        "config"
    ]
    
    created_dirs = []
    failed_dirs = []
    
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            logger.debug(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            failed_dirs.append(str(full_path))
    
    if failed_dirs:
        logger.error(f"Failed to create {len(failed_dirs)} directories.")
        return False
    
    logger.info(f"Successfully created {len(created_dirs)} directories for project {root_dir}.")
    return True

def main():
    """Entry point for script execution."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Default project path as specified in the task
    project_root = "projects/PROJ-064-statistical-discrepancies-in-publicly-av"
    
    success = initialize_project_structure(project_root)
    
    if success:
        print(f"Project structure initialized successfully at: {project_root}")
        sys.exit(0)
    else:
        print(f"Failed to initialize project structure at: {project_root}")
        sys.exit(1)

if __name__ == "__main__":
    main()
