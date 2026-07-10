import os
from pathlib import Path
import logging

from utils import get_project_root_path, ensure_directory

logger = logging.getLogger(__name__)

def setup_data_structure():
    """
    Creates the required data directory structure for the project:
    - data/raw/
    - data/processed/
    - data/qc/

    This corresponds to Task T001b.
    """
    project_root = get_project_root_path()
    data_root = project_root / "data"

    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "qc",
    ]

    created_count = 0
    for directory in directories:
        if ensure_directory(directory):
            logger.info(f"Created directory: {directory}")
            created_count += 1
        else:
            logger.info(f"Directory already exists: {directory}")

    logger.info(f"Data structure setup complete. {created_count} new directories created.")
    return True
