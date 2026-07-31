import os
import sys
import logging
from pathlib import Path

# Import existing utilities from the project API surface
from utils.logging import get_logger
from utils.config import get_project_root, get_data_dir

def create_data_directories(logger: logging.Logger) -> None:
    """
    Creates the required directory structure for the data pipeline.
    
    Creates:
        data/raw/          - Raw ingested data (e.g., ZINC15 chunks)
        data/processed/    - Preprocessed data with features
        data/splits/       - Train/test split indices
        data/schemas/      - Schema definition files
    
    Args:
        logger: Logger instance for recording directory creation status.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    # Ensure the base data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Base data directory ensured: {data_dir}")
    
    # Define subdirectories to create
    subdirectories = [
        "raw",
        "processed",
        "splits",
        "schemas"
    ]
    
    for subdir in subdirectories:
        dir_path = data_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created/Verified directory: {dir_path}")

def main() -> int:
    """
    Main entry point for creating the data directory structure.
    
    Returns:
        int: 0 on success, 1 on failure.
    """
    logger = get_logger(__name__)
    logger.info("Starting data directory structure creation for task T001b...")
    
    try:
        create_data_directories(logger)
        logger.info("Data directory structure creation completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create data directory structure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())