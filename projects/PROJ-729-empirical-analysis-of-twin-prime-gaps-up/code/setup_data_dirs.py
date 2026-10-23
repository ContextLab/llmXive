import sys
import logging
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
    if logger is None:
        # Fallback to a basic logger if the caller monkey‑patched setup_logging
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            logging.basicConfig(level=logging.INFO)

    logger.info("Initializing data directory structure for twin prime gap analysis.")

    try:
        config = get_config()
        # ensure_directories creates the base data path and the specific subdirectories
        # defined in the project specification.
        base_dir = ensure_directories([
            config['paths']['raw'],
            config['paths']['results'],
            config['paths']['figures'],
        ])

        logger.info(f"Data directory structure verified/created at: {base_dir}")
        logger.info("  - data/raw/")
        logger.info("  - data/results/")
        logger.info("  - data/figures/")

        return 0
    except Exception as e:
        exit_with_error(f"Failed to setup data directories: {e}")

if __name__ == "__main__":
    sys.exit(main())