import os
import sys
from pathlib import Path
import logging
from utils.logging import get_logger

def ensure_data_directory():
    """
    Creates the 'data' directory at the project root if it does not exist.
    Verifies existence via pathlib.
    """
    logger = get_logger(__name__)
    
    # Determine project root (parent of code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    data_dir = project_root / "data"

    if not data_dir.exists():
        logger.info(f"Creating data directory at: {data_dir}")
        data_dir.mkdir(parents=True, exist_ok=True)
    else:
        logger.info(f"Data directory already exists at: {data_dir}")

    # Verification step as required by task T001b
    if not (Path(__file__).parent.parent.joinpath('data').is_dir()):
        raise RuntimeError("Verification failed: data directory was not created.")
    
    logger.info("Data directory verification successful.")
    return data_dir

def main():
    """Entry point for script execution."""
    setup_logging()
    ensure_data_directory()
    logger = get_logger(__name__)
    logger.info("T001b completed: data/ directory created and verified.")

if __name__ == "__main__":
    main()
