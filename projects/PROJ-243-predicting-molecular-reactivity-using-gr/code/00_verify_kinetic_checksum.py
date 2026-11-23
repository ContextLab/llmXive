import os
import sys
import hashlib
import logging
from typing import Dict, Optional

from config import get_config

def load_manifest(manifest_path: str) -> Dict:
    """Load the checksums manifest JSON."""
    import json
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest not found at {manifest_path}")
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """Verify the SHA-256 checksum of a file against an expected value."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for verification: {file_path}")
    
    actual_hash = calculate_sha256(file_path)
    return actual_hash == expected_hash

def main():
    """
    T009e: Verify checksum (SHA-256) of the downloaded kinetic_dataset_raw.csv.
    
    This script:
    1. Loads the manifest from data/raw/checksums.json.
    2. Checks if the expected hash is 'pending'.
       - If 'pending', it calculates the hash, updates the manifest, and logs success.
       - If a valid hash exists, it verifies the file against it.
    3. Exits with error code 1 if verification fails or file is missing.
    """
    config = get_config()
    manifest_path = os.path.join(config['paths']['data_raw'], 'checksums.json')
    target_filename = 'kinetic_dataset_raw.csv'
    target_path = os.path.join(config['paths']['data_raw'], target_filename)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    logger.info(f"Starting checksum verification for {target_filename}")

    # 1. Load Manifest
    try:
        manifest = load_manifest(manifest_path)
    except FileNotFoundError as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)

    if target_filename not in manifest:
        logger.error(f"Target file '{target_filename}' not found in manifest.")
        sys.exit(1)

    file_info = manifest[target_filename]
    expected_hash = file_info.get('hash')

    # 2. Check if file exists
    if not os.path.exists(target_path):
        logger.error(f"Target file does not exist: {target_path}")
        logger.error("Prerequisite T009d (Download) may not have completed successfully.")
        sys.exit(1)

    # 3. Verification Logic
    if expected_hash == 'pending':
        logger.info(f"Hash in manifest is 'pending'. Calculating hash for {target_filename}...")
        actual_hash = calculate_sha256(target_path)
        logger.info(f"Calculated hash: {actual_hash}")
        
        # Update manifest
        file_info['hash'] = actual_hash
        file_info['status'] = 'verified_on_fetch'
        
        import json
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Updated manifest with new hash for {target_filename}.")
        logger.info("Verification successful (hash recorded).")
    else:
        logger.info(f"Verifying {target_filename} against stored hash...")
        try:
            is_valid = verify_checksum(target_path, expected_hash)
            if is_valid:
                logger.info("Checksum verification PASSED.")
            else:
                actual_hash = calculate_sha256(target_path)
                logger.error(f"Checksum verification FAILED.")
                logger.error(f"Expected: {expected_hash}")
                logger.error(f"Actual:   {actual_hash}")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error during verification: {e}")
            sys.exit(1)

    logger.info("T009e completed successfully.")

if __name__ == "__main__":
    main()
