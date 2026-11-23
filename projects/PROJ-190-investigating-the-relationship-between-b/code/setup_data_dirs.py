import os
from pathlib import Path
from typing import List
from utils.logging import get_logger, info, warning, error

# Import ensure_directories from config to maintain API consistency
from config import ensure_directories

logger = get_logger(__name__)

def create_data_directories() -> None:
    """
    Create the required directory structure for data storage.
    
    Creates:
      - data/raw/          : For raw downloaded data (HCP fMRI, scores)
      - data/processed/    : For preprocessed time series and metrics
      - data/results/      : For final analysis results and reports
    """
    # Define the relative paths required by the project
    # These match the paths specified in tasks.md T007
    required_dirs: List[Path] = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/results"),
    ]

    # Use the existing ensure_directories utility from config.py
    # to create these paths, ensuring consistent behavior with
    # the rest of the project's configuration handling.
    ensure_directories(required_dirs)
    
    for dir_path in required_dirs:
        full_path = Path.cwd() / dir_path
        if full_path.exists():
            info(f"Directory created or already exists: {full_path}")
        else:
            error(f"Failed to create directory: {full_path}")
            raise RuntimeError(f"Directory creation failed for {full_path}")

def main() -> None:
    """
    Entry point for the directory setup script.
    """
    logger.info("Starting data directory setup (T007)...")
    try:
        create_data_directories()
        logger.info("Data directory structure successfully created.")
    except Exception as e:
        logger.error(f"Directory setup failed: {e}")
        raise