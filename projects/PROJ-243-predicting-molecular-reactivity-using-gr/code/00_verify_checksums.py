import os
import sys
import hashlib
import logging
from typing import Optional

from config import get_config

# Ensure the logging is configured if not already done by the runner
try:
    logging.getLogger().handlers
except IndexError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def load_manifest(manifest_path: str) -> dict:
    """
    Loads the SHA-256 manifest file.
    Expects a text file with lines formatted as: <hash> <filename>
    or a JSON file with a mapping of filename -> hash.
    For this implementation, we support the standard 'sha256sum' text format.
    """
    manifest = {}
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Standard sha256sum format: "hash  filename" or "hash *filename"
            parts = line.split()
            if len(parts) >= 2:
                # Handle potential asterisk prefix for binary mode indicator
                filename = parts[1].lstrip('*').lstrip(' ')
                checksum = parts[0]
                manifest[filename] = checksum.lower()
            elif len(parts) == 1:
                # If just a hash is provided, assume it's for the file named in context or a specific mapping
                # But standard format requires filename. We'll log a warning if format is weird.
                logging.warning(f"Skipping malformed manifest line: {line}")
    
    return manifest

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Computes SHA-256 of the file at file_path and compares it to expected_hash.
    Returns True if they match, False otherwise.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        computed_hash = sha256_hash.hexdigest().lower()
        
        if computed_hash == expected_hash:
            logging.info(f"Checksum verification PASSED for {file_path}")
            logging.info(f"  Computed: {computed_hash}")
            logging.info(f"  Expected: {expected_hash}")
            return True
        else:
            logging.error(f"Checksum verification FAILED for {file_path}")
            logging.error(f"  Computed: {computed_hash}")
            logging.error(f"  Expected: {expected_hash}")
            return False
    except Exception as e:
        logging.error(f"Error computing checksum for {file_path}: {e}")
        return False

def main():
    """
    Main entry point for verifying the checksum of reference_substructures_raw.csv.
    """
    config = get_config()
    
    # Define paths based on project structure
    # The raw file should be at data/raw/reference_substructures_raw.csv
    # The manifest should be at data/raw/reference_substructures_raw.csv.sha256 or similar
    raw_file_name = "reference_substructures_raw.csv"
    raw_file_path = os.path.join(config['data_raw_dir'], raw_file_name)
    
    # Common manifest naming conventions
    possible_manifests = [
        os.path.join(config['data_raw_dir'], f"{raw_file_name}.sha256"),
        os.path.join(config['data_raw_dir'], "checksums.sha256"),
        os.path.join(config['data_raw_dir'], "manifest.json")
    ]
    
    manifest_path = None
    for p in possible_manifests:
        if os.path.exists(p):
            manifest_path = p
            break
    
    if not manifest_path:
        logging.error(f"No manifest file found for {raw_file_name}. "
                      f"Searched: {possible_manifests}")
        sys.exit(1)
    
    logging.info(f"Using manifest: {manifest_path}")
    
    if not os.path.exists(raw_file_path):
        logging.error(f"Raw data file not found: {raw_file_path}")
        logging.error("Please ensure T009a (Download) has been completed successfully.")
        sys.exit(1)
    
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logging.error(f"Failed to load manifest: {e}")
        sys.exit(1)
    
    # Look for the specific file in the manifest
    expected_hash = None
    # Try exact filename first
    if raw_file_name in manifest:
        expected_hash = manifest[raw_file_name]
    else:
        # Try to find it if the manifest has a different path prefix
        for fname, h in manifest.items():
            if fname.endswith(raw_file_name):
                expected_hash = h
                logging.info(f"Found matching entry in manifest: {fname}")
                break
    
    if not expected_hash:
        logging.error(f"File '{raw_file_name}' not found in manifest {manifest_path}")
        logging.error(f"Available entries: {list(manifest.keys())}")
        sys.exit(1)
    
    success = verify_checksum(raw_file_path, expected_hash)
    
    if not success:
        logging.error("Verification failed. Exiting with error code 1.")
        sys.exit(1)
    else:
        logging.info("Verification successful. Exiting with code 0.")
        sys.exit(0)

if __name__ == "__main__":
    main()
