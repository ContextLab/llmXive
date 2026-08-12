"""
Script to initialize data directories for the molecular surface area prediction project.
Creates the directory structure required for data ingestion, processing, and splitting.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.logging import get_logger
from code.utils.config import get_project_root


def create_data_directories(logger: logging.Logger) -> None:
    """
    Create the required data directories under the project root.

    Directories to create:
    - data/raw/
    - data/processed/
    - data/splits/
    - data/schemas/

    Args:
        logger: Logger instance for status messages.
    """
    project_root = get_project_root()
    data_base = project_root / "data"

    directories = [
        "raw",
        "processed",
        "splits",
        "schemas",
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = data_base / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Data directory initialization complete. Created {created_count} new directories.")


def main() -> None:
    """Main entry point for the script."""
    logger = get_logger("setup_data_structure")
    logger.info("Starting data directory initialization...")

    try:
        create_data_directories(logger)
        logger.info("Data directory initialization successful.")
    except Exception as e:
        logger.error(f"Data directory initialization failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()