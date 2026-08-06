"""
Task T010b: Verify checksum of reference_substructures_raw.csv against checksums.json.

This script loads the expected SHA-256 hash from data/raw/checksums.json
and compares it against the calculated hash of data/raw/reference_substructures_raw.csv.
It exits with code 0 on success and code 1 on failure.
"""
import os
import sys
import json
import hashlib
import logging

# Add parent directory to path to allow relative imports if run as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from utils.checksum_manager import calculate_sha256, load_checksums


def setup_script_logging():
    """Initialize logging for this script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def verify_reference_checksum(logger):
    """
    Verify the checksum of the reference substructures raw file.

    Returns:
        bool: True if verification passes, False otherwise.
    """
    config = get_config()
    raw_dir = config.get('paths', {}).get('raw', 'data/raw')
    checksums_path = os.path.join(raw_dir, 'checksums.json')
    target_file_name = 'reference_substructures_raw.csv'
    target_file_path = os.path.join(raw_dir, target_file_name)

    # 1. Check if target file exists
    if not os.path.exists(target_file_path):
        logger.error(f"Target file not found: {target_file_path}")
        logger.error("Task T010a (Fetch Reference Set) must complete before T010b.")
        return False

    # 2. Check if checksums manifest exists
    if not os.path.exists(checksums_path):
        logger.error(f"Checksum manifest not found: {checksums_path}")
        logger.error("Task T010g (Create Checksums) must complete before T010b.")
        return False

    # 3. Load expected checksums
    try:
        expected_hashes = load_checksums(checksums_path)
    except Exception as e:
        logger.error(f"Failed to load checksums manifest: {e}")
        return False

    # 4. Retrieve expected hash for the specific file
    if 'reference_substructures' not in expected_hashes:
        logger.error(f"Expected hash for 'reference_substructures' not found in {checksums_path}")
        return False

    expected_hash = expected_hashes['reference_substructures'].get('sha256')
    if not expected_hash:
        logger.error(f"No 'sha256' key found for 'reference_substructures' in manifest.")
        return False

    logger.info(f"Expected hash: {expected_hash}")

    # 5. Calculate actual hash
    try:
        actual_hash = calculate_sha256(target_file_path)
    except Exception as e:
        logger.error(f"Failed to calculate SHA-256 for {target_file_path}: {e}")
        return False

    logger.info(f"Actual hash:   {actual_hash}")

    # 6. Compare
    if actual_hash.lower() == expected_hash.lower():
        logger.info(f"SUCCESS: Checksum verification passed for {target_file_name}.")
        return True
    else:
        logger.error(f"FAILURE: Checksum mismatch for {target_file_name}.")
        logger.error(f"   Expected: {expected_hash}")
        logger.error(f"   Actual:   {actual_hash}")
        logger.error("Data corruption or incorrect download detected.")
        return False


def main():
    logger = setup_script_logging()
    logger.info("Starting T010b: Verify reference substructures checksum.")

    success = verify_reference_checksum(logger)

    if success:
        logger.info("T010b completed successfully.")
        sys.exit(0)
    else:
        logger.error("T010b failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()