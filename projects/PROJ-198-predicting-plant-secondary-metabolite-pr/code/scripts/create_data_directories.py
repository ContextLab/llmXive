"""
Script to create the data directory structure for the project.
Ensures data/raw, data/processed, and data/interim exist.
"""
import os
import sys
from pathlib import Path
import logging

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import setup_logging, get_logger
from config_env import ensure_directories

def main():
    """
    Main entry point for creating data directories.
    """
    # Setup logging
    logger = setup_logging()
    logger.info("Starting data directory creation process.")

    # Define the required data directories relative to project root
    # Assuming the script is run from the project root or code/scripts
    project_root = Path(__file__).parent.parent.parent
    data_root = project_root / "data"

    required_dirs = [
        data_root,
        data_root / "raw",
        data_root / "processed",
        data_root / "interim"
    ]

    # Use the ensure_directories helper from config_env if available,
    # or create them manually to ensure they exist.
    # The config_env ensure_directories likely handles the main project structure,
    # but we explicitly ensure data subdirs here as per task T001b.
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Data directory structure verification complete. {created_count} directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
