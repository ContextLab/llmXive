import os
import sys
import logging
from pathlib import Path
from utils.logging_config import setup_pipeline_logger
from utils.setup_dirs import setup_project_structure

def main():
    """
    Entry point for the project setup script.
    Creates the required directory structure as per T001a.
    """
    logger = setup_pipeline_logger("main_setup")
    logger.info("Starting project directory structure setup...")

    try:
        setup_project_structure()
        logger.info("Directory structure created successfully.")
    except Exception as e:
        logger.error(f"Failed to create directory structure: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Setup complete.")

if __name__ == "__main__":
    main()
