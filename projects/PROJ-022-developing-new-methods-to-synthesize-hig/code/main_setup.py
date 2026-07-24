"""
Main entry point for project setup.
Creates the required directory structure for the llmXive pipeline.
"""
import os
import sys
import logging
from pathlib import Path
from utils.logging_config import setup_pipeline_logger
from utils.setup_dirs import setup_project_structure

def main():
    """
    Entry point to initialize the project directory structure.
    """
    logger = setup_pipeline_logger("main_setup")
    logger.info("Starting project directory structure setup...")

    # Define the required directories relative to the project root
    # The project root is assumed to be the current working directory
    root = Path.cwd()

    # Directories to create as per T001a
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "artifacts"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")

    logger.info(f"Setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
