"""
Script to create the required data directory structure for the project.
Creates data/raw/, data/processed/, and data/consent/ directories.
Each directory will contain a .gitkeep file to ensure they are tracked by git.
"""
import os
from pathlib import Path

from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir
from logging_config import setup_logging, get_logger


def create_directory_structure():
    """
    Create the necessary data sub-directories and populate them with .gitkeep files.

    Directories created:
    - data/raw/
    - data/processed/
    - data/consent/

    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    logger = get_logger()
    project_root = get_project_root()
    directories = [
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir()
    ]

    success = True
    for dir_path in directories:
        try:
            # Ensure the path is relative to project root and exists
            if not dir_path.is_absolute():
                dir_path = project_root / dir_path

            logger.info(f"Creating directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)

            gitkeep_path = dir_path / ".gitkeep"
            gitkeep_path.touch(exist_ok=True)
            logger.info(f"Created .gitkeep in {dir_path}")

        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False

    return success


def main():
    """Entry point for the directory setup script."""
    setup_logging()
    logger = get_logger()
    logger.info("Starting data directory creation...")

    if create_directory_structure():
        logger.info("Data directory structure created successfully.")
        return 0
    else:
        logger.error("Failed to create some data directories.")
        return 1


if __name__ == "__main__":
    exit(main())
