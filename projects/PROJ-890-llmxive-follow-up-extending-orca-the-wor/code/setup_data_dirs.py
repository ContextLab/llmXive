"""
Script to initialize the data directory structure and generate the initial checksum manifest.
This script ensures that `data/raw/`, `data/processed/`, and `data/validation/` exist
and creates a baseline `checksum_manifest.json`.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.checksum_utils import initialize_data_structure, generate_checksum_manifest

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for data directory initialization.
    """
    # Define the data directory relative to project root
    data_dir = project_root / "data"
    
    logger.info(f"Initializing data directory structure at: {data_dir}")
    
    # 1. Create the directory structure
    initialize_data_structure(data_dir)
    
    # 2. Generate the initial checksum manifest
    # Even if empty, this establishes the baseline for future verification
    try:
        manifest_path = generate_checksum_manifest(data_dir)
        logger.info(f"Initialization complete. Manifest saved to: {manifest_path}")
    except FileNotFoundError as e:
        logger.error(f"Failed to initialize: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
