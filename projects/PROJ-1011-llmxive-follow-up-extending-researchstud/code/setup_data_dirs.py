import argparse
import sys
from pathlib import Path
import logging

from utils.data_manifest import create_directory_structure

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for setting up the data directory structure.
    Creates raw, processed, and results directories and initializes the manifest.
    """
    parser = argparse.ArgumentParser(description="Setup data directory structure for llmXive project.")
    parser.add_argument(
        "--data-root",
        type=str,
        default="data",
        help="Path to the data root directory (default: data)"
    )
    args = parser.parse_args()

    data_root = Path(args.data_root)
    logger.info(f"Setting up data directory structure at: {data_root.absolute()}")

    try:
        create_directory_structure(data_root)
        logger.info("Data directory structure setup completed successfully.")
    except Exception as e:
        logger.error(f"Failed to setup data directory structure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
