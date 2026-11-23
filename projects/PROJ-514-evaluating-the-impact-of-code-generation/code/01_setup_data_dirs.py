"""
Script to setup the data directory structure for the project.
This script creates the necessary directories for storing raw, intermediate,
processed data, as well as reports and reference sets.
"""
import os
import sys
from pathlib import Path
from utils.logger import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

def setup_data_directories():
    """
    Creates the required data directory structure relative to the project root.
    
    Directories created:
    - data/raw/human_samples
    - data/raw/llm_samples
    - data/raw/reference_set
    - data/intermediate
    - data/processed
    - reports
    """
    project_root = get_project_root()
    data_root = project_root / "data"
    
    # Define the directory structure to create
    directories = [
        data_root / "raw" / "human_samples",
        data_root / "raw" / "llm_samples",
        data_root / "raw" / "reference_set",
        data_root / "intermediate",
        data_root / "processed",
        project_root / "reports",
    ]
    
    created_count = 0
    existing_count = 0
    
    for directory in directories:
        try:
            # Create directory with parents if they don't exist
            directory.mkdir(parents=True, exist_ok=True)
            
            # Verify the directory is writable
            test_file = directory / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
                created_count += 1
                logger.info(f"Successfully created and verified writable: {directory}")
            except (OSError, PermissionError) as e:
                logger.error(f"Directory {directory} created but not writable: {e}")
                # Don't count as successfully created if not writable
                if directory.exists():
                    directory.rmdir() # Clean up empty directory
        except Exception as e:
            logger.error(f"Failed to create directory {directory}: {e}")
    
    logger.info(f"Data directory setup complete. Created: {created_count}, Existing: {existing_count}")
    return created_count == len(directories)

def main():
    """Main entry point for the script."""
    logger.info("Starting data directory setup...")
    success = setup_data_directories()
    
    if success:
        logger.info("Data directory structure is ready.")
        sys.exit(0)
    else:
        logger.error("Data directory setup failed. Please check permissions.")
        sys.exit(1)

if __name__ == "__main__":
    main()
