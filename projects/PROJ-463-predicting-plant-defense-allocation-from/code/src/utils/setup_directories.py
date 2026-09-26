"""
Directory setup utilities.
"""
import os
import sys
from pathlib import Path
from typing import List
import logging

from .config import get_data_path

logger = logging.getLogger(__name__)

def setup_data_directories() -> None:
    """
    Create the required directory structure for the project.
    """
    data_path = get_data_path()

    directories = [
        data_path / "raw",
        data_path / "processed",
        data_path / "traits",
        data_path / "manifests",
        data_path / "synthetic"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")

    # Create flag file
    flag_file = data_path / ".dir_setup_complete"
    flag_file.touch()
    logger.info(f"Created flag file: {flag_file}")

def main():
    """
    Main entry point for directory setup.
    """
    setup_data_directories()
    return 0

if __name__ == "__main__":
    sys.exit(main())