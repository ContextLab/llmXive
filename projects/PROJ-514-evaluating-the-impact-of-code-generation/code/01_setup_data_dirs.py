"""
Setup script for creating the data directory structure.

This script creates the required directories for storing raw, intermediate,
and processed data as defined in the project plan.

Directories created:
- data/raw/human_samples
- data/raw/llm_samples
- data/intermediate
- data/processed
"""
import os
import sys
from pathlib import Path
from utils.logger import get_logger
from utils.config import get_project_root


def setup_data_directories():
    """
    Create the required data directory structure.
    
    Returns:
        dict: A dictionary mapping directory names to their absolute paths.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    data_root = project_root / "data"
    
    # Define the required directories
    required_dirs = [
        data_root / "raw" / "human_samples",
        data_root / "raw" / "llm_samples",
        data_root / "intermediate",
        data_root / "processed",
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in required_dirs:
        try:
            # Create parents if they don't exist
            dir_path.mkdir(parents=True, exist_ok=True)
            
            if dir_path.exists() and dir_path.is_dir():
                if dir_path.is_dir() and len(list(dir_path.iterdir())) == 0:
                    # New directory created
                    created_count += 1
                    logger.info(f"Created directory: {dir_path}")
                else:
                    # Directory already existed
                    existing_count += 1
                    logger.info(f"Directory already exists: {dir_path}")
            else:
                logger.error(f"Failed to create directory: {dir_path}")
                return False
        except PermissionError:
            logger.error(f"Permission denied creating directory: {dir_path}")
            return False
        except Exception as e:
            logger.error(f"Error creating directory {dir_path}: {e}")
            return False
    
    logger.info(f"Data directory setup complete. Created: {created_count}, Existing: {existing_count}")
    return True


def main():
    """Main entry point for the script."""
    logger = get_logger(__name__)
    logger.info("Starting data directory setup...")
    
    success = setup_data_directories()
    
    if success:
        logger.info("Data directory setup completed successfully.")
        sys.exit(0)
    else:
        logger.error("Data directory setup failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
