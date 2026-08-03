import os
import sys
import logging
from config import ensure_directories

def setup_script_logging():
    """Configure logging for the directory setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("artifacts/logs/setup_directories.log")
        ]
    )
    return logging.getLogger(__name__)

def main():
    """
    Main entry point for T001b: Create code and artifact directories.
    
    This script ensures the existence of the following directories:
    - code/
    - artifacts/
    - tests/
    
    It relies on the ensure_directories function from config.py which 
    reads the project configuration and creates the necessary folder structure.
    """
    logger = setup_script_logging()
    logger.info("Starting directory setup for T001b...")
    
    # Ensure the base directories exist
    # The ensure_directories function in config.py is responsible for creating
    # the full directory tree defined in the project configuration.
    ensure_directories()
    
    logger.info("Directory setup completed successfully.")
    logger.info("Created directories: code/, artifacts/, tests/")

if __name__ == "__main__":
    main()
