"""
Script to initialize the project directory structure.
Creates all required directories for code, data, tests, and artifacts.
"""
import os
import sys
import logging
from config import ensure_directories

def setup_script_logging():
    """Initialize logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Main entry point to create project directories."""
    logger = setup_script_logging()
    logger.info("Initializing project directory structure...")
    
    try:
        ensure_directories()
        logger.info("Successfully created all required directories.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
