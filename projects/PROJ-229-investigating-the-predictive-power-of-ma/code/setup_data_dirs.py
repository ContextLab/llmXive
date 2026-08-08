"""
Script to create the required data directory structure for the project.

This task (T001a) ensures the following directories exist:
- data/raw
- data/processed
- data/results
- data/external

It uses the project's config to determine the root path and logs the operations.
"""
import os
import logging
from pathlib import Path
from typing import List

# Importing from the project's config module as per API surface
from config import get_config

# Importing logger utility as per API surface
from code.utils.logger import get_pipeline_logger

def create_data_directories() -> None:
    """
    Creates the standard data directory structure.
    
    Raises:
        OSError: If directory creation fails for any reason.
    """
    logger = get_pipeline_logger()
    config = get_config()
    
    # Determine the project root. 
    # Assuming the script runs from the project root or we use the config's base path.
    # If config specifies a base_dir, use that; otherwise, assume current working directory.
    base_path = Path(config.get("base_dir", "."))
    
    data_dirs = [
        "raw",
        "processed",
        "results",
        "external"
    ]
    
    created_count = 0
    for dir_name in data_dirs:
        target_path = base_path / "data" / dir_name
        try:
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {target_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {target_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {target_path}: {e}")
            raise e
    
    logger.info(f"Data directory setup complete. Created {created_count} new directories.")

def main() -> None:
    """
    Entry point for the script.
    """
    try:
        create_data_directories()
    except Exception as e:
        # Use the project's error handling if available, or standard logging
        logging.error(f"Script failed: {e}")
        raise e

if __name__ == "__main__":
    main()
