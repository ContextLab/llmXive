"""
Directory setup utility for the llmXive research pipeline.
Creates the required data directory structure as per task T004.
"""
import logging
import sys
from pathlib import Path
from code.config import PROJECT_ROOT
from code.utils.logger import setup_logger


def create_directory_structure(logger: logging.Logger) -> bool:
    """
    Creates the required data directory structure:
    - data/raw/
    - data/processed/
    - data/validation/
    - results/

    Args:
        logger: The logger instance to use for logging.

    Returns:
        True if all directories were created successfully, False otherwise.
    """
    # Define the directories to create relative to PROJECT_ROOT
    directories = [
        "data/raw",
        "data/processed",
        "data/validation",
        "results",
    ]

    success = True
    for dir_path_str in directories:
        dir_path = PROJECT_ROOT / dir_path_str
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            else:
                logger.debug(f"Directory already exists: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False

    return success


def main() -> None:
    """Main entry point for directory setup."""
    logger = setup_logger()
    logger.info("Starting directory structure setup...")

    if create_directory_structure(logger):
        logger.info("Directory structure setup completed successfully.")
        sys.exit(0)
    else:
        logger.error("Directory structure setup failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()