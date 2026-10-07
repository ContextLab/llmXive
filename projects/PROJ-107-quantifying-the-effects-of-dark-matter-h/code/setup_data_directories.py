"""
Script to create the required data directory structure for the project.
Implements Task T001b.
"""
import os
import sys
from pathlib import Path
import logging

# Add project root to path to import utils if needed, though this script is standalone
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_project_root

def setup_data_directories():
    """
    Creates the data directory structure as defined in T001b:
    - data/
      - raw/
        - tng100/
        - millennium/
      - processed/
      - metadata/
    """
    project_root = get_project_root()
    data_root = project_root / "data"

    # Define subdirectories relative to data_root
    subdirs = [
        "raw/tng100",
        "raw/millennium",
        "processed",
        "metadata"
    ]

    created_dirs = []

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info(f"Setting up data directories under: {data_root}")

    for subdir in subdirs:
        full_path = data_root / subdir
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path.relative_to(project_root)))
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            return False

    logger.info(f"Successfully created {len(created_dirs)} directories.")
    return True

def main():
    """Entry point for the script."""
    success = setup_data_directories()
    if success:
        print("Data directory structure created successfully.")
        sys.exit(0)
    else:
        print("Failed to create data directory structure.")
        sys.exit(1)

if __name__ == "__main__":
    main()