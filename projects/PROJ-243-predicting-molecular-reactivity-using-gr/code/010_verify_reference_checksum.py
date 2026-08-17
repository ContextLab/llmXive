import os
import sys
import json
import hashlib
import logging
from typing import Optional
from config import get_config, ensure_directories

def setup_script_logging():
    """Initialize logging for the checksum verification script."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

def calculate_sha256(file_path: str) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: str) -> dict:
    """Load the checksums manifest JSON file."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def verify_reference_checksum(logger: Optional[logging.Logger] = None) -> bool:
    """
    Verify the SHA-256 checksum of data/raw/reference_substructures_raw.csv
    against the hash stored in data/raw/checksums.json.

    Returns:
        bool: True if verification passes, False otherwise.
    """
    if logger is None:
        logger = setup_script_logging()

    config = get_config()
    ensure_directories(config)

    file_path = os.path.join(config['paths']['data_raw'], 'reference_substructures_raw.csv')
    manifest_path = os.path.join(config['paths']['data_raw'], 'checksums.json')

    # Check if files exist
    if not os.path.exists(file_path):
        logger.error(f"Target file not found: {file_path}")
        return False

    if not os.path.exists(manifest_path):
        logger.error(f"Manifest file not found: {manifest_path}")
        return False

    try:
        # Load expected checksum
        manifest = load_manifest(manifest_path)
        expected_checksum = manifest.get('reference_substructures_raw.csv')
        
        if expected_checksum is None:
            logger.error(f"Checksum for 'reference_substructures_raw.csv' not found in manifest.")
            return False

        # Calculate actual checksum
        logger.info(f"Calculating SHA-256 for {file_path}...")
        actual_checksum = calculate_sha256(file_path)

        logger.info(f"Expected: {expected_checksum}")
        logger.info(f"Actual:   {actual_checksum}")

        if actual_checksum == expected_checksum:
            logger.info("Checksum verification PASSED.")
            return True
        else:
            logger.error("Checksum verification FAILED. The file may be corrupted or modified.")
            return False

    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False

def main():
    """Entry point for the script."""
    logger = setup_script_logging()
    success = verify_reference_checksum(logger)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
