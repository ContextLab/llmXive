import os
import logging
from pathlib import Path
from config import ensure_directories
from logging_config import setup_logging, get_logger

def create_gitkeep(directory_path: Path) -> None:
    """
    Creates a .gitkeep file in the specified directory to ensure
    the directory is tracked by git even if it is empty.
    
    Args:
        directory_path: Path to the directory where .gitkeep should be created.
    """
    gitkeep_path = directory_path / ".gitkeep"
    if not gitkeep_path.exists():
        try:
            # Create parent directories if they don't exist
            directory_path.mkdir(parents=True, exist_ok=True)
            # Create an empty .gitkeep file
            gitkeep_path.touch()
            logging.info(f"Created .gitkeep in {directory_path}")
        except OSError as e:
            logging.error(f"Failed to create .gitkeep in {directory_path}: {e}")
            raise

def main() -> None:
    """
    Main entry point for setting up the data directory structure.
    Creates required directories and initializes .gitkeep files.
    """
    logger = get_logger()
    logger.info("Starting data directory setup...")

    # Define the required directory structure relative to project root
    # Assuming standard project layout: data/raw/landsat, data/processed, data/ecotourism
    base_data_dir = Path("data")
    
    directories_to_create = [
        base_data_dir / "raw" / "landsat",
        base_data_dir / "processed",
        base_data_dir / "ecotourism"
    ]

    # Ensure base data directory exists
    ensure_directories(str(base_data_dir))

    for directory in directories_to_create:
        try:
            create_gitkeep(directory)
        except Exception as e:
            logger.error(f"Error creating directory structure for {directory}: {e}")
            raise

    logger.info("Data directory structure setup complete.")

if __name__ == "__main__":
    setup_logging()
    main()