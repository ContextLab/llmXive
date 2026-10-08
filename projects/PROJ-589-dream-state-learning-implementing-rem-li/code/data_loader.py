"""
Data loading orchestration script for the Dream-State Learning project.

This script handles the downloading and verification of datasets (GLUE/SuperGLUE)
required for training and evaluation. It is invoked by the run-book (quickstart.md).

Usage:
    python code/data_loader.py --download
"""
import argparse
import sys
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import Config
from data.loader import verify_dataset_integrity, load_glue_subset
from utils.logger import get_logger
from utils.exceptions import DataIntegrityError

logger = get_logger(__name__)

def download_datasets():
    """
    Download and verify all configured datasets.
    """
    config = Config()
    logger.info("Starting dataset download and verification process.")
    
    datasets_to_load = []
    
    # Check GLUE subsets
    if config.glue_subsets:
        for subset in config.glue_subsets:
            datasets_to_load.append(("glue", subset))
    
    # Check SuperGLUE subsets
    if config.superglue_subsets:
        for subset in config.superglue_subsets:
            datasets_to_load.append(("superglue", subset))

    if not datasets_to_load:
        logger.warning("No datasets configured in config.py. Skipping download.")
        return

    for dataset_type, subset_name in datasets_to_load:
        logger.info(f"Processing {dataset_type.upper()} subset: {subset_name}")
        
        try:
            # This triggers the download via the datasets library
            # and performs checksum verification internally if configured
            dataset = load_glue_subset(subset_name) if dataset_type == "glue" else None
            
            # Verify integrity (this will raise DataIntegrityError if checksum fails)
            verify_dataset_integrity(subset_name)
            
            logger.info(f"Successfully downloaded and verified {subset_name}.")
            
        except DataIntegrityError as e:
            logger.error(f"Data integrity check failed for {subset_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to download/verify {subset_name}: {e}")
            raise

    logger.info("All datasets downloaded and verified successfully.")

def main():
    parser = argparse.ArgumentParser(description="Data loading and verification script.")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download and verify all configured datasets."
    )
    
    args = parser.parse_args()

    if args.download:
        download_datasets()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()