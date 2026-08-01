import os
import sys
import hashlib
import logging
from typing import Dict, Optional

from config import get_config

def load_manifest(manifest_path: str) -> Dict[str, str]:
    """
    Load the SHA-256 manifest file.
    Expected format: one line per file, 'hash  filename' or 'hash,filename'.
    Returns a dict mapping filename -> hash.
    """
    manifest = {}
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Support space or comma separation
            parts = line.replace(',', ' ').split()
            if len(parts) >= 2:
                # Take the last part as filename if there are more than 2 parts
                # to handle cases like "hash  path/to/file.csv"
                filename = parts[-1]
                checksum = parts[0]
                manifest[filename] = checksum
    return manifest

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Calculate SHA-256 of file_path and compare with expected_hash.
    Returns True if they match, False otherwise.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_hash = sha256_hash.hexdigest()
        return actual_hash == expected_hash
    except Exception as e:
        logging.error(f"Error reading file {file_path} for checksum: {e}")
        return False

def main():
    """
    Main entry point for verifying the kinetic dataset checksum.
    Expects:
      - data/raw/kinetic_dataset_raw.csv (downloaded by T009d)
      - data/raw/kinetic_dataset_raw.csv.sha256 (or similar manifest)
    
    This script verifies the checksum of the kinetic dataset against the manifest.
    It exits with code 0 on success, 1 on failure.
    """
    logger = logging.getLogger(__name__)
    config = get_config()
    
    # Define paths based on project conventions
    # The download task (T009d) should have placed the file here.
    # The manifest is expected to be alongside the raw file or in a specific manifest dir.
    # We assume the manifest is named 'kinetic_dataset_raw.csv.sha256' or similar.
    # If T009d created a manifest, we look for it.
    
    raw_file_path = os.path.join(config['data_dir'], 'raw', 'kinetic_dataset_raw.csv')
    
    if not os.path.exists(raw_file_path):
        logger.error(f"Kinetic dataset raw file not found: {raw_file_path}")
        logger.error("Please ensure T009d (download) has completed successfully.")
        sys.exit(1)
    
    # Look for manifest file. Common conventions:
    # 1. <filename>.sha256
    # 2. <filename>.manifest
    # 3. checksums.txt
    manifest_candidates = [
        f"{raw_file_path}.sha256",
        f"{raw_file_path}.manifest",
        os.path.join(os.path.dirname(raw_file_path), 'checksums.txt'),
        os.path.join(config['data_dir'], 'raw', 'kinetic_dataset_manifest.txt')
    ]
    
    manifest_path = None
    for candidate in manifest_candidates:
        if os.path.exists(candidate):
            manifest_path = candidate
            break
    
    if not manifest_path:
        logger.error("No manifest file found for kinetic dataset checksum verification.")
        logger.error("Expected one of: " + ", ".join(manifest_candidates))
        sys.exit(1)
    
    logger.info(f"Found manifest at: {manifest_path}")
    
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)
    
    # Determine the key to look for in the manifest.
    # It should match the basename of the raw file.
    target_filename = os.path.basename(raw_file_path)
    
    if target_filename not in manifest:
        logger.error(f"Filename '{target_filename}' not found in manifest.")
        logger.error(f"Available entries: {list(manifest.keys())}")
        sys.exit(1)
    
    expected_hash = manifest[target_filename]
    logger.info(f"Verifying checksum for {target_filename}...")
    logger.info(f"Expected SHA-256: {expected_hash}")
    
    if verify_checksum(raw_file_path, expected_hash):
        logger.info(f"SUCCESS: Checksum verified for {target_filename}.")
        sys.exit(0)
    else:
        logger.error(f"FAILURE: Checksum mismatch for {target_filename}.")
        sys.exit(1)

if __name__ == "__main__":
    # Basic logging setup if not already configured by the project's logging infra
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
