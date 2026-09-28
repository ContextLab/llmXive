import os
import sys
from pathlib import Path
from config import get_config_from_args
from utils.logger import get_logger

def main():
    """
    Setup directory structure for data/raw and data/processed.
    This script ensures the required directories exist before data processing begins.
    """
    logger = get_logger("setup_data_dirs")
    config = get_config_from_args()
    project_root = Path(config.project_root)
    
    # Define required directories
    data_raw_dir = project_root / "data" / "raw"
    data_processed_dir = project_root / "data" / "processed"
    
    # Create directories if they don't exist
    for directory in [data_raw_dir, data_processed_dir]:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
        else:
            logger.info(f"Directory already exists: {directory}")
    
    logger.info("Data directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())