"""
Script to create necessary project directories.
Ensures the existence of 'code', 'artifacts', and 'tests' directories.
"""
import os
import sys
import logging
from typing import List
from config import get_config, ensure_directories


def setup_script_logging() -> logging.Logger:
    """
    Sets up logging for the script.
    Returns a logger instance.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def create_directories(logger: logging.Logger, dirs: List[str]) -> None:
    """
    Creates the specified directories if they do not exist.

    Args:
        logger: The logger instance to use for logging.
        dirs: A list of directory paths to create.
    """
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.info(f"Directory already exists: {dir_path}")


def main() -> int:
    """
    Main entry point for the script.
    Creates the required project directories.
    Returns 0 on success, 1 on failure.
    """
    logger = setup_script_logging()
    logger.info("Starting directory creation process.")

    # Define the directories to create based on T002 requirements
    # The task explicitly asks for: 'code', 'artifacts', 'tests'
    # We also ensure 'artifacts/logs' and 'artifacts/weights' exist for downstream tasks
    required_dirs = [
        "code",
        "artifacts",
        "artifacts/logs",
        "artifacts/weights",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
    ]

    try:
        create_directories(logger, required_dirs)
        logger.info("Directory creation process completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())