"""
Script to create the required data directory structure.
Creates 'raw' and 'processed' subdirectories under 'data/'.
"""
import os
from pathlib import Path
from code.config import ensure_dirs
from code.utils.logging import get_logger

def setup_data_directories():
    """
    Creates the data directory structure:
    - data/raw/
    - data/processed/

    Uses the ensure_dirs function from config to handle creation.
    """
    logger = get_logger(__name__)
    logger.info("Starting data directory setup...")

    # Define the base data directory
    base_dir = Path("data")
    raw_dir = base_dir / "raw"
    processed_dir = base_dir / "processed"

    # Ensure the base directory exists
    ensure_dirs(str(base_dir))

    # Create subdirectories
    ensure_dirs(str(raw_dir))
    ensure_dirs(str(processed_dir))

    logger.info(f"Created directory: {raw_dir}")
    logger.info(f"Created directory: {processed_dir}")
    logger.info("Data directory setup complete.")

    return True

if __name__ == "__main__":
    success = setup_data_directories()
    if success:
        print("Data directories created successfully.")
    else:
        print("Failed to create data directories.")
        exit(1)