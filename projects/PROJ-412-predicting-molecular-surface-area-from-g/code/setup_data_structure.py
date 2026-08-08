import os
import sys
import logging
from pathlib import Path
from code.utils.logging import get_logger
from code.utils.config import get_project_root, get_data_dir

def create_data_directories():
    """
    Creates the required directory structure for the data pipeline.
    
    Directories created:
    - data/raw/
    - data/processed/
    - data/splits/
    - data/schemas/
    
    Returns:
        list: A list of created directory paths.
    """
    logger = get_logger("setup_data_structure")
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    directories = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "splits",
        data_dir / "schemas"
    ]
    
    created_paths = []
    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(dir_path))
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise
    
    return created_paths

def main():
    """Main entry point for creating data directory structure."""
    logger = setup_logging("setup_data_structure")
    logger.info("Starting data directory structure creation...")
    
    try:
        created = create_data_directories()
        logger.info(f"Successfully created {len(created)} directories.")
        for path in created:
            logger.info(f"  - {path}")
        return 0
    except Exception as e:
        logger.error(f"Error creating data directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())