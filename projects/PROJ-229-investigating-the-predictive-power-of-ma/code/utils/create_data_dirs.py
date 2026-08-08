"""
Script to create the data directory structure for the project.
Creates: data/raw, data/processed, data/results, data/external
"""
import os
import logging
from pathlib import Path
from typing import List

from config import get_config
from code.utils.logger import get_pipeline_logger

def create_data_directories(logger: logging.Logger) -> List[Path]:
    """
    Creates the required data directories based on the project configuration.
    
    Args:
        logger: The logger instance to record creation actions.
        
    Returns:
        A list of Path objects for the created directories.
    """
    config = get_config()
    base_dir = Path(config.get("data_dir", "data"))
    
    # Define required subdirectories
    required_dirs = [
        "raw",
        "processed",
        "results",
        "external"
    ]
    
    created_paths = []
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")
        created_paths.append(dir_path)
        
    return created_paths

def main():
    """Main entry point for the script."""
    logger = get_pipeline_logger()
    logger.info("Starting data directory creation...")
    
    try:
        paths = create_data_directories(logger)
        logger.info(f"Successfully created/verified {len(paths)} data directories.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create data directories: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
