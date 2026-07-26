"""
Script to download and verify the MSD and AMT datasets.
This script implements the logic from T013 (download_datasets) and T062/T063.
It is invoked by the quickstart run-book to populate data/raw/.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data_ingestion import download_datasets
from config import get_project_root, get_config_dict
from utils import setup_logging

def main():
    """
    Orchestrates the download of raw datasets.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting data download process...")
    
    try:
        # This function handles:
        # 1. Fetching MSD and AMT from canonical URLs (config.MSD_URL, config.AMT_URL)
        # 2. Streaming large datasets to avoid RAM overflow
        # 3. Validating checksums
        # 4. Failing loudly if sources are unreachable (no synthetic fallback)
        download_datasets()
        
        logger.info("Data download and verification completed successfully.")
        
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        # Fail loudly as per constraints
        raise

if __name__ == "__main__":
    main()