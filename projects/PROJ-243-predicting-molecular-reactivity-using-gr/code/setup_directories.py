import os
import sys
import logging
from typing import List
from config import get_config, ensure_directories

def setup_script_logging():
    """Configure logging for the directory setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_directories(logger: logging.Logger, dirs: List[str]) -> None:
    """
    Create the specified directories if they do not exist.
    
    Args:
        logger: Logger instance for status updates.
        dirs: List of relative directory paths to create.
    """
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
            logger.info(f"Created directory: {d}")
        else:
            logger.info(f"Directory already exists: {d}")

def main():
    """Main entry point for directory setup."""
    logger = setup_script_logging()
    logger.info("Starting directory setup for project structure.")
    
    # Define the required directories based on T002
    required_dirs = [
        "code",
        "artifacts",
        "tests",
        # Ensure data subdirectories exist as per T001a/b/c context
        "data/raw",
        "data/processed",
        "data/assets"
    ]
    
    create_directories(logger, required_dirs)
    
    logger.info("Directory setup completed successfully.")

if __name__ == "__main__":
    main()
