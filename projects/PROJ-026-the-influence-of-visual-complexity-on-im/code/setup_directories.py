"""
Module to set up the project directory structure.
Creates required folders for stimuli, responses, processed data, and results.
"""
import os
from pathlib import Path
import logging
from config import get_project_root

# Configure logger
logger = logging.getLogger(__name__)

def setup_directories():
    """
    Creates the required directory structure for the project.
    Specifically creates:
    - data/raw/stimuli
    - data/raw/responses
    - data/processed
    - data/results
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    project_root = get_project_root()
    data_root = project_root / "data"
    
    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw/stimuli",
        "data/raw/responses",
        "data/processed",
        "data/results"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {full_path}")
                existing_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            return False
    
    logger.info(f"Directory setup complete. Created: {created_count}, Existing: {existing_count}")
    return True

def main():
    """
    Entry point for the setup_directories script.
    """
    # Set up basic logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    logger.info("Starting directory setup...")
    success = setup_directories()
    
    if success:
        logger.info("Directory setup completed successfully.")
        return 0
    else:
        logger.error("Directory setup failed.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())