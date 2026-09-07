"""
Script to create the data directory structure and .gitkeep files.
This ensures the directory hierarchy exists for raw, processed, and ecotourism data.
"""
import os
from pathlib import Path
from config import ensure_directories
from logging_config import setup_logging, get_logger

def main():
    """
    Creates the required data directory structure:
    - data/raw/landsat
    - data/processed
    - data/ecotourism

    Also creates .gitkeep files in each directory to ensure they are tracked by git.
    """
    setup_logging()
    logger = get_logger(__name__)

    # Define the required directories relative to the project root
    # We assume the script is run from the project root or code/
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"

    directories = [
        data_root / "raw" / "landsat",
        data_root / "processed",
        data_root / "ecotourism"
    ]

    logger.info(f"Ensuring data directories exist at: {data_root}")
    
    # Use the existing utility to ensure directories exist
    ensure_directories([str(d) for d in directories])

    # Create .gitkeep files in each directory to preserve them in git
    for directory in directories:
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            try:
                gitkeep_path.touch()
                logger.info(f"Created .gitkeep file at: {gitkeep_path}")
            except OSError as e:
                logger.error(f"Failed to create .gitkeep at {gitkeep_path}: {e}")
        else:
            logger.debug(f".gitkeep already exists at: {gitkeep_path}")

    logger.info("Data directory structure setup complete.")

if __name__ == "__main__":
    main()
