import os
import sys
import hashlib
import logging
from typing import Optional, Dict

# Import project config for paths and logging setup
from config import get_config, ensure_directories
from utils.logging_utils import setup_logging, get_logger

def load_manifest(manifest_path: str) -> Dict[str, str]:
    """
    Load the SHA-256 manifest file.
    Expected format: one line per file: 'sha256_hash  filename'
    Returns a dict mapping filename -> expected_hash.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    manifest = {}
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Handle standard checksum output format: <hash>  <filename>
            parts = line.split()
            if len(parts) >= 2:
                # Take the last part as filename (handles spaces in names if formatted as hash  name)
                # Usually format is: <hash> <filename> or <hash>  <filename>
                file_hash = parts[0]
                filename = parts[-1] 
                manifest[filename] = file_hash
            elif len(parts) == 1:
                # Fallback if only hash is present (unlikely but safe)
                pass
    return manifest

def verify_checksum(file_path: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """
    Compute the checksum of the file at file_path and compare it to expected_hash.
    Returns True if they match, False otherwise.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File to verify not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)

    computed_hash = hash_func.hexdigest()
    return computed_hash.lower() == expected_hash.lower()

def main():
    """
    Main entry point for T009b: Verify checksum of reference_substructures_raw.csv.
    """
    config = get_config()
    logger = setup_logging("verify_checksums")
    
    # Paths defined in config/project structure
    # The task T009a should have produced this file
    raw_file_path = os.path.join(config['paths']['data_raw'], 'reference_substructures_raw.csv')
    
    # The manifest should be alongside the raw file or in a specific location
    # We assume the manifest is named <filename>.sha256 or exists in the same dir
    manifest_path = os.path.join(config['paths']['data_raw'], 'reference_substructures_raw.csv.sha256')
    
    # If the specific .sha256 file doesn't exist, try to look for a general manifest
    if not os.path.exists(manifest_path):
        # Fallback: check if a generic manifest exists in data_raw
        manifest_path = os.path.join(config['paths']['data_raw'], 'manifest.sha256')
        
    logger.info(f"Verifying checksum for: {raw_file_path}")
    
    if not os.path.exists(raw_file_path):
        logger.error(f"Target file missing: {raw_file_path}")
        # Ensure the directory exists so the next run (T009a) can create it
        ensure_directories(config)
        sys.exit(1)

    if not os.path.exists(manifest_path):
        logger.error(f"Manifest file missing: {manifest_path}")
        sys.exit(1)

    try:
        manifest = load_manifest(manifest_path)
        filename = os.path.basename(raw_file_path)
        
        if filename not in manifest:
            logger.error(f"Filename '{filename}' not found in manifest.")
            sys.exit(1)
        
        expected_hash = manifest[filename]
        
        if verify_checksum(raw_file_path, expected_hash):
            logger.info(f"Checksum verification PASSED for {filename}.")
            logger.info(f"  Expected: {expected_hash}")
            # Log the computed hash for transparency
            computed_hash = hashlib.sha256(open(raw_file_path, 'rb').read()).hexdigest()
            logger.info(f"  Computed: {computed_hash}")
            sys.exit(0)
        else:
            computed_hash = hashlib.sha256(open(raw_file_path, 'rb').read()).hexdigest()
            logger.error(f"Checksum verification FAILED for {filename}.")
            logger.error(f"  Expected: {expected_hash}")
            logger.error(f"  Computed: {computed_hash}")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Verification process failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
