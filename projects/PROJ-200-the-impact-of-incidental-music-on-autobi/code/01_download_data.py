import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to allow imports from code/
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from data_ingestion import download_datasets
from config import get_project_root, get_config_dict

logger = logging.getLogger(__name__)

def main():
    """
    Orchestrate the data download pipeline for User Story 1.
    1. Download datasets (T013)
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Data Download Pipeline (T118)...")

    root = get_project_root()
    config = get_config_dict()

    # 1. Download Datasets (T013)
    logger.info("Step 1: Downloading datasets...")
    # The download_datasets function handles the streaming and downloading.
    # It is expected to download the MSD and AMT datasets to data/raw/
    # and verify their checksums.

    try:
        # We assume download_datasets handles the download and verification.
        # If it returns data, we might need to handle it, but the task says it downloads to disk.
        download_datasets()
        logger.info("Datasets downloaded successfully.")
    except Exception as e:
        logger.error(f"Failed to download datasets: {e}")
        raise

    logger.info("Data Download Pipeline completed.")

if __name__ == "__main__":
    main()
