"""
Script to create the required data directory structure and .gitkeep files.

This task (T008) ensures the following directories exist:
- data/raw/landsat
- data/processed
- data/ecotourism

It creates .gitkeep files in each directory to ensure they are tracked by git.
"""
import os
import logging
from pathlib import Path
from config import ensure_directories
from logging_config import setup_logging, get_logger

# Define the required directories relative to the project root
DATA_DIRS = [
    "data/raw/landsat",
    "data/processed",
    "data/ecotourism"
]

def create_gitkeep(directory_path: Path) -> None:
    """
    Create a .gitkeep file in the specified directory.
    
    Args:
        directory_path: Path to the directory where .gitkeep should be created.
    """
    gitkeep_path = directory_path / ".gitkeep"
    try:
        with open(gitkeep_path, 'w') as f:
            f.write("# This file ensures the directory is tracked by git.\n")
        logging.info(f"Created .gitkeep at: {gitkeep_path}")
    except Exception as e:
        logging.error(f"Failed to create .gitkeep at {gitkeep_path}: {e}")
        raise

def main():
    """
    Main entry point to create data directories and .gitkeep files.
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("Starting data directory setup (T008)...")
    
    # Ensure the base 'data' directory exists
    data_root = Path("data")
    ensure_directories([str(data_root)])
    
    # Create subdirectories and .gitkeep files
    for dir_str in DATA_DIRS:
        dir_path = data_root / dir_str
        try:
            # Create the directory (parents=True to create intermediate dirs if needed)
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {dir_path}")
            
            # Create .gitkeep
            create_gitkeep(dir_path)
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

    logger.info("Data directory structure setup complete.")

if __name__ == "__main__":
    main()
