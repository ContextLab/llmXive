"""
Data validation utilities for the llmXive project.
Provides functions to ensure data directory structure and validate checksums.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from utils.config import get_data_raw_dir, get_data_processed_dir
from utils.hasher import hash_file, generate_manifest, verify_manifest

logger = logging.getLogger(__name__)

DATA_RAW_DIR = get_data_raw_dir()
DATA_PROCESSED_DIR = get_data_processed_dir()
MANIFEST_RAW = DATA_RAW_DIR / ".manifest.json"
MANIFEST_PROCESSED = DATA_PROCESSED_DIR / ".manifest.json"


def ensure_data_structure() -> bool:
    """
    Ensure that the required data directory structure exists.
    Creates directories if they are missing.

    Returns:
        bool: True if structure is valid (created or existing), False on error.
    """
    try:
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty manifests if they don't exist
        if not MANIFEST_RAW.exists():
            generate_manifest(DATA_RAW_DIR, MANIFEST_RAW)
            logger.info(f"Initialized manifest for raw data at {MANIFEST_RAW}")
        
        if not MANIFEST_PROCESSED.exists():
            generate_manifest(DATA_PROCESSED_DIR, MANIFEST_PROCESSED)
            logger.info(f"Initialized manifest for processed data at {MANIFEST_PROCESSED}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to ensure data structure: {e}")
        return False


def validate_raw_data() -> Tuple[bool, List[str]]:
    """
    Validate the integrity of raw data files against the manifest.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_failed_files)
    """
    if not MANIFEST_RAW.exists():
        logger.warning("Raw data manifest not found. Running initial scan...")
        if not generate_manifest(DATA_RAW_DIR, MANIFEST_RAW):
            return False, ["Failed to generate initial manifest"]
        return True, []

    try:
        is_valid, failed_files = verify_manifest(MANIFEST_RAW)
        if not is_valid:
            logger.error(f"Raw data validation failed for {len(failed_files)} files")
        else:
            logger.info("Raw data validation passed")
        return is_valid, failed_files
    except Exception as e:
        logger.error(f"Error validating raw data: {e}")
        return False, [str(e)]


def validate_processed_data() -> Tuple[bool, List[str]]:
    """
    Validate the integrity of processed data files against the manifest.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_failed_files)
    """
    if not MANIFEST_PROCESSED.exists():
        logger.warning("Processed data manifest not found. Running initial scan...")
        if not generate_manifest(DATA_PROCESSED_DIR, MANIFEST_PROCESSED):
            return False, ["Failed to generate initial manifest"]
        return True, []

    try:
        is_valid, failed_files = verify_manifest(MANIFEST_PROCESSED)
        if not is_valid:
            logger.error(f"Processed data validation failed for {len(failed_files)} files")
        else:
            logger.info("Processed data validation passed")
        return is_valid, failed_files
    except Exception as e:
        logger.error(f"Error validating processed data: {e}")
        return False, [str(e)]


def refresh_manifests() -> bool:
    """
    Regenerate manifests for both raw and processed data directories.
    This should be called after new data is added or modified.

    Returns:
        bool: True if both manifests were successfully refreshed, False otherwise.
    """
    success_raw = generate_manifest(DATA_RAW_DIR, MANIFEST_RAW)
    success_processed = generate_manifest(DATA_PROCESSED_DIR, MANIFEST_PROCESSED)
    
    if success_raw:
        logger.info(f"Refreshed manifest for raw data: {MANIFEST_RAW}")
    if success_processed:
        logger.info(f"Refreshed manifest for processed data: {MANIFEST_PROCESSED}")
        
    return success_raw and success_processed


def main():
    """
    Main entry point for running validation checks from the command line.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting data validation...")
    
    # Ensure structure exists
    if not ensure_data_structure():
        logger.error("Failed to ensure data structure")
        return 1
    
    # Validate raw data
    raw_valid, raw_failures = validate_raw_data()
    if not raw_valid:
        logger.warning(f"Raw data validation issues: {raw_failures}")
    
    # Validate processed data
    processed_valid, processed_failures = validate_processed_data()
    if not processed_valid:
        logger.warning(f"Processed data validation issues: {processed_failures}")
    
    # Refresh manifests
    if not refresh_manifests():
        logger.error("Failed to refresh manifests")
        return 1
    
    logger.info("Data validation completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
