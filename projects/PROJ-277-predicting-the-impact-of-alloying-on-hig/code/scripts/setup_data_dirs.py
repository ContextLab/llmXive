"""
Script to initialize the data directory structure for the project.
Creates 'data/raw' and 'data/processed' directories as required by T008.
"""
import os
import sys
from pathlib import Path

# Add the parent directory of 'scripts' to the path to allow imports from 'code'
# Assuming this script is located at code/scripts/setup_data_dirs.py
current_dir = Path(__file__).resolve().parent
code_root = current_dir.parent
project_root = code_root.parent

# Ensure the project root is in sys.path for relative imports if needed
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config_from_args
from utils.logger import get_logger

def main():
    # Parse arguments to get the mode (ci/local) which might affect path logic
    # although for directory creation, the base paths are usually constant.
    # We use the config utility to ensure consistency with T005.
    config = get_config_from_args()
    logger = get_logger(__name__)

    logger.info("Starting data directory setup (Task T008)...")

    # Define the base data directory relative to the project root
    data_dir = project_root / "data"
    
    # Define subdirectories
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create directories if they don't exist
    directories = [raw_dir, processed_dir]
    
    for dir_path in directories:
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            except OSError as e:
                logger.error(f"Failed to create directory {dir_path}: {e}")
                sys.exit(1)
        else:
            logger.info(f"Directory already exists: {dir_path}")

    logger.info("Data directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())