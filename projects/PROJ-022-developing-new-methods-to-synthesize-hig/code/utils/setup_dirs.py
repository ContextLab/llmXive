"""
Utility functions for setting up project directories.
"""
import os
import sys
from pathlib import Path
import logging
from utils.logging_config import setup_pipeline_logger

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The Path object representing the directory.

    Returns:
        True if the directory was created or already existed, False on error.
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            return True
        return True
    except OSError as e:
        logging.getLogger(__name__).error(f"Failed to create directory {path}: {e}")
        return False

def setup_project_structure(root_dir: Path) -> None:
    """
    Sets up the standard directory structure for the llmXive pipeline.

    Args:
        root_dir: The root directory of the project.
    """
    logger = logging.getLogger(__name__)
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "artifacts"
    ]

    for d in dirs:
        target = root_dir / d
        if ensure_directory(target):
            logger.info(f"Ensured directory: {target}")

def main():
    """
    CLI entry point for directory setup.
    """
    logger = setup_pipeline_logger("setup_dirs")
    logger.info("Running setup_dirs module directly.")
    root = Path.cwd()
    setup_project_structure(root)
    logger.info("Directory structure setup complete.")

if __name__ == "__main__":
    main()
