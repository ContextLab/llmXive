import sys
from pathlib import Path
from code.utils.checksum_tracker import initialize_directories, track_directory
from code.utils.logger import setup_logging, get_logger
from code.config import get_path

def main():
    """
    Task T006: Create data/raw/ and data/processed/ directory structure with checksum tracking.
    
    This script initializes the required data directories and sets up the checksum
    registry to track file integrity for all data artifacts produced by the pipeline.
    """
    logger = setup_logging()
    logger.info("Starting data directory structure setup (Task T006)...")

    # Define the root data directory
    data_root = Path(get_path("data_root"))
    
    # Define required subdirectories
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    figures_dir = data_root / "figures"
    intermediates_dir = data_root / "intermediates"

    # Initialize directories and checksum tracking
    # This creates the directories if they don't exist and initializes the registry
    initialize_directories([raw_dir, processed_dir, figures_dir, intermediates_dir])
    
    logger.info(f"Created directory structure under: {data_root}")
    logger.info(f"  - raw: {raw_dir}")
    logger.info(f"  - processed: {processed_dir}")
    logger.info(f"  - figures: {figures_dir}")
    logger.info(f"  - intermediates: {intermediates_dir}")

    # Initialize the checksum registry for the raw and processed directories
    # This ensures that any files added later will be tracked
    try:
        track_directory(raw_dir)
        track_directory(processed_dir)
        logger.info("Checksum tracking initialized for raw and processed directories.")
    except Exception as e:
        logger.error(f"Failed to initialize checksum tracking: {e}")
        sys.exit(1)

    logger.info("Data directory structure setup completed successfully.")

if __name__ == "__main__":
    main()
