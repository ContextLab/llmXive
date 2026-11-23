import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import yaml

from utils.config import get_project_root, get_data_processed_path
from analysis.metadata_utils import flag_all_output_datasets

logger = logging.getLogger(__name__)

def main():
    """
    Main entry point to update metadata for all output datasets.
    This ensures the associational_only flag is present in metadata.yaml
    for all required files.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starting metadata update for output datasets...")
    
    try:
        flag_all_output_datasets()
        logger.info("Metadata update completed successfully.")
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")
        raise

if __name__ == "__main__":
    main()
