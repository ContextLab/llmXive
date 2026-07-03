import sys
from pathlib import Path
from config import get_config, ensure_directories
from utils import setup_logging, exit_with_error

def main():
    """
    Setup the data directory structure:
    - data/raw/
    - data/results/
    - data/figures/
    
    This script is idempotent; it will create directories if they do not exist
    and exit successfully if they already exist.
    """
    logger = setup_logging()
    logger.info("Initializing data directory structure for twin prime gap analysis.")
    
    try:
        config = get_config()
        # ensure_directories creates the base data path and the specific subdirectories
        # defined in the project specification.
        base_dir = ensure_directories(config)
        
        logger.info(f"Data directory structure verified/created at: {base_dir}")
        logger.info("  - data/raw/")
        logger.info("  - data/results/")
        logger.info("  - data/figures/")
        
        return 0
    except Exception as e:
        exit_with_error(f"Failed to setup data directories: {e}")

if __name__ == "__main__":
    sys.exit(main())
