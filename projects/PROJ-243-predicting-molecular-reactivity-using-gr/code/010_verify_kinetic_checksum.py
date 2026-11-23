"""
Task T010e: Verify checksum (SHA-256) of data/raw/kinetic_dataset_raw.csv
against the hash in data/raw/checksums.json.
"""
import os
import sys
import json
import hashlib
import logging
from typing import Dict, Optional

# Add project root to path for imports if running as script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import get_config

def setup_script_logging(name: str = "verify_kinetic_checksum") -> logging.Logger:
    """Configure logging for the script."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: str) -> Dict:
    """Load the checksums manifest JSON."""
    with open(manifest_path, 'r') as f:
        return json.load(f)

def verify_checksum(actual_hash: str, expected_hash: str, file_path: str) -> bool:
    """
    Verify the actual hash against the expected hash.
    Returns True if they match, False otherwise.
    """
    if actual_hash == expected_hash:
        return True
    else:
        logging.error(f"Checksum mismatch for {file_path}")
        logging.error(f"  Expected: {expected_hash}")
        logging.error(f"  Actual:   {actual_hash}")
        return False

def verify_kinetic_checksum(config: Dict, logger: Optional[logging.Logger] = None) -> bool:
    """
    Verify the checksum of the kinetic dataset raw file.
    
    Returns:
        bool: True if verification passes, False otherwise.
    """
    if logger is None:
        logger = setup_script_logging()

    kinetic_file_path = os.path.join(config['paths']['raw_data'], 'kinetic_dataset_raw.csv')
    manifest_path = os.path.join(config['paths']['raw_data'], 'checksums.json')

    logger.info(f"Verifying checksum for: {kinetic_file_path}")
    
    if not os.path.exists(kinetic_file_path):
        logger.error(f"File not found: {kinetic_file_path}")
        return False

    if not os.path.exists(manifest_path):
        logger.error(f"Manifest not found: {manifest_path}")
        return False

    # Calculate actual hash
    try:
        actual_hash = calculate_sha256(kinetic_file_path)
        logger.info(f"Calculated SHA-256: {actual_hash}")
    except Exception as e:
        logger.error(f"Failed to calculate hash: {e}")
        return False

    # Load manifest
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return False

    # Get expected hash
    expected_hash = None
    if 'files' in manifest and kinetic_file_path in manifest['files']:
        expected_hash = manifest['files'][kinetic_file_path].get('sha256')
    
    if expected_hash is None:
        logger.error(f"Expected hash not found in manifest for {kinetic_file_path}")
        return False

    logger.info(f"Expected SHA-256:   {expected_hash}")

    # Verify
    is_valid = verify_checksum(actual_hash, expected_hash, kinetic_file_path)
    
    if is_valid:
        logger.info("Checksum verification PASSED.")
    else:
        logger.error("Checksum verification FAILED.")

    return is_valid

def main():
    """Main entry point for the script."""
    logger = setup_script_logging()
    logger.info("Starting kinetic dataset checksum verification (Task T010e).")
    
    try:
        config = get_config()
        success = verify_kinetic_checksum(config, logger)
        
        if success:
            logger.info("Task T010e completed successfully.")
            sys.exit(0)
        else:
            logger.error("Task T010e failed: Checksum mismatch or file missing.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()