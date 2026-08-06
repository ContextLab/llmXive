"""
Task T010e: Verify checksum (SHA-256) of data/raw/kinetic_dataset_raw.csv.

This script validates the integrity of the downloaded kinetic dataset
against the expected hash stored in data/raw/checksums.json.

It relies on the existing infrastructure:
- code/config.py for paths and configuration
- code/utils/checksum_manager.py for calculation and verification logic
"""
import os
import sys
import json
import logging
from typing import Dict, Optional

# Add project root to path for imports if running as script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import get_config
from utils.checksum_manager import calculate_sha256, load_checksums

def setup_script_logging():
    """Configure logging for this verification script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(get_config()['paths']['logs'], 'verify_kinetic_checksum.log'))
        ]
    )
    return logging.getLogger(__name__)

def verify_kinetic_checksum(logger: logging.Logger) -> bool:
    """
    Verify the SHA-256 checksum of the kinetic dataset.

    Returns:
        bool: True if verification passes, False otherwise.

    Raises:
        FileNotFoundError: If the raw kinetic dataset or checksums file is missing.
        ValueError: If the checksums file is malformed.
    """
    config = get_config()
    raw_dir = config['paths']['raw']
    checksums_file = os.path.join(raw_dir, 'checksums.json')
    target_file = os.path.join(raw_dir, 'kinetic_dataset_raw.csv')

    # 1. Validate input files exist
    if not os.path.exists(target_file):
        error_msg = f"Target file not found: {target_file}. Ensure T010d (Download Kinetic Dataset) has completed successfully."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    if not os.path.exists(checksums_file):
        error_msg = f"Checksums manifest not found: {checksums_file}. Ensure T010g/T010h (Checksums Setup) has completed successfully."
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # 2. Load expected checksums
    try:
        expected_checksums = load_checksums(checksums_file)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse checksums manifest: {e}")
        raise ValueError(f"Invalid checksums manifest: {e}")

    # 3. Identify the specific key for the kinetic dataset
    # The schema defines 'kinetic_dataset' as the key for the local static asset file.
    expected_key = 'kinetic_dataset'
    if expected_key not in expected_checksums:
        error_msg = f"Key '{expected_key}' not found in checksums manifest. Available keys: {list(expected_checksums.keys())}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    expected_hash = expected_checksums[expected_key]['hash']
    source_info = expected_checksums[expected_key].get('source', 'Unknown')
    version = expected_checksums[expected_key].get('version', 'Unknown')

    logger.info(f"Verifying integrity for: {os.path.basename(target_file)}")
    logger.info(f"  Source: {source_info}")
    logger.info(f"  Version: {version}")
    logger.info(f"  Expected Hash: {expected_hash}")

    # 4. Calculate actual hash
    actual_hash = calculate_sha256(target_file)
    logger.info(f"  Actual Hash:   {actual_hash}")

    # 5. Compare
    if actual_hash == expected_hash:
        logger.info("SUCCESS: Checksum verification passed. Data integrity confirmed.")
        return True
    else:
        error_msg = (
            f"FAILURE: Checksum mismatch for {os.path.basename(target_file)}.\n"
            f"  Expected: {expected_hash}\n"
            f"  Actual:   {actual_hash}\n"
            f"  Action: Re-run the download script (T010d) to ensure the file is not corrupted."
        )
        logger.error(error_msg)
        return False

def main():
    """Main entry point for the verification script."""
    logger = setup_script_logging()
    try:
        success = verify_kinetic_checksum(logger)
        if success:
            logger.info("Task T010e completed successfully.")
            sys.exit(0)
        else:
            logger.error("Task T010e failed: Checksum mismatch.")
            sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"Task T010e failed: Missing required file - {e}")
        sys.exit(2)
    except ValueError as e:
        logger.error(f"Task T010e failed: Configuration error - {e}")
        sys.exit(3)
    except Exception as e:
        logger.exception(f"Task T010e failed with unexpected error: {e}")
        sys.exit(4)

if __name__ == '__main__':
    main()