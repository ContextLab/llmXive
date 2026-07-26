import os
import sys
import hashlib
import logging
from typing import Dict, Optional

# Import existing utilities from the project
from config import get_config
from utils.loaders import calculate_sha256

def load_manifest(manifest_path: str) -> Dict[str, str]:
    """
    Load the SHA-256 manifest file.
    Expected format: one line per file, whitespace separated:
    <sha256_hash>  <filename>
    or
    <sha256_hash>  <relative_path>
    """
    manifest = {}
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 2:
                # Handle cases where filename might have spaces but usually it doesn't in manifests
                # Standard checksum format: hash  filename
                file_hash = parts[0]
                filename = parts[-1] 
                manifest[filename] = file_hash
            else:
                logging.warning(f"Skipping malformed manifest line: {line}")
    
    return manifest

def verify_checksum(file_path: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected hash.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    computed_hash = calculate_sha256(file_path)
    
    if computed_hash.lower() == expected_hash.lower():
        logging.info(f"Checksum verified successfully for {file_path}")
        logging.info(f"  Expected: {expected_hash}")
        logging.info(f"  Computed: {computed_hash}")
        return True
    else:
        logging.error(f"Checksum MISMATCH for {file_path}")
        logging.error(f"  Expected: {expected_hash}")
        logging.error(f"  Computed: {computed_hash}")
        return False

def main():
    """
    Main entry point for verifying the kinetic dataset checksum.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    config = get_config()
    
    # Define paths based on project structure
    # T009d downloads to data/raw/kinetic_dataset_raw.csv
    raw_data_dir = os.path.join(config.data_root, "raw")
    kinetic_file_name = "kinetic_dataset_raw.csv"
    kinetic_file_path = os.path.join(raw_data_dir, kinetic_file_name)
    
    # The manifest is typically alongside the raw data or in a specific manifest dir.
    # We assume a manifest file exists named 'kinetic_manifest.txt' in the raw data directory
    # or we look for a generic manifest.
    manifest_path = os.path.join(raw_data_dir, "kinetic_manifest.txt")
    
    if not os.path.exists(manifest_path):
        # Fallback: check if manifest is in the root of data/raw
        # If the task T009d logic created a manifest, it should be here.
        # If not, we fail loudly as per constraints.
        logging.error(f"Manifest file not found at {manifest_path}. "
                      "Cannot verify checksum without a source manifest.")
        sys.exit(1)

    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logging.error(f"Failed to load manifest: {e}")
        sys.exit(1)

    if kinetic_file_name not in manifest:
        logging.error(f"File '{kinetic_file_name}' not found in manifest.")
        sys.exit(1)

    expected_hash = manifest[kinetic_file_name]

    try:
        is_valid = verify_checksum(kinetic_file_path, expected_hash)
        if is_valid:
            logging.info("Verification PASSED.")
            sys.exit(0)
        else:
            logging.error("Verification FAILED.")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Verification process failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()