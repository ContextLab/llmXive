"""
Script to create the data directory structure for the project.
Creates data/raw/, data/processed/, and data/consent/ directories.
Ensures each directory contains a .gitkeep file to preserve them in version control.
"""
import os
from pathlib import Path
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir
from logging_config import setup_logging, get_logger

logger = get_logger()

def create_directory_structure(base_path: Path):
    """
    Create the required data directory structure.
    
    Args:
        base_path: The root path where data directories will be created.
    """
    directories = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir()
    ]
    
    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            
            # Create .gitkeep file to ensure directory is tracked by git
            gitkeep_path = dir_path / ".gitkeep"
            gitkeep_path.touch(exist_ok=True)
            logger.info(f"Created .gitkeep in: {dir_path}")
            
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

def main():
    """Main entry point for the script."""
    setup_logging()
    logger.info("Starting data directory structure setup")
    
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")
    
    create_directory_structure(project_root)
    
    logger.info("Data directory structure setup completed successfully")

if __name__ == "__main__":
    main()
