import os
from pathlib import Path
import logging

def create_project_directories():
    """
    Create the required directory structure for the project.
    Specifically creates:
    - projects/PROJ-530-neural-correlates-of-error-monitoring-du/data/raw/
    - projects/PROJ-530-neural-correlates-of-error-monitoring-du/data/processed/
    
    Returns:
        bool: True if all directories were created successfully.
    """
    base_path = Path("projects/PROJ-530-neural-correlates-of-error-monitoring-du")
    data_raw = base_path / "data" / "raw"
    data_processed = base_path / "data" / "processed"
    
    directories = [data_raw, data_processed]
    
    logger = logging.getLogger(__name__)
    
    success = True
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory created: {directory}")
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            success = False
            
    return success

def main():
    """Entry point for directory creation script."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting directory creation for PROJ-530...")
    if create_project_directories():
        logger.info("Directory creation completed successfully.")
    else:
        logger.error("Directory creation failed.")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
