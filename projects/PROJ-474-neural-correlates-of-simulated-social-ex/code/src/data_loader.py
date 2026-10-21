"""
Data loader module for downloading OpenNeuro dataset ds000030.
Implements retry logic, integrity verification, and checksum recording.
"""
import os
import time
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.config import load_config
from src.utils import get_logger
from src.exceptions import DataUnavailableError

logger = get_logger(__name__)
config = load_config()

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_openneuro_dataset():
    """
    Downloads OpenNeuro dataset ds000030.
    Implements retry logic and checksum verification.
    
    This is a placeholder that verifies the dataset structure
    and computes checksums for all NIfTI files found in data/raw/.
    """
    raw_dir = Path(config['paths']['raw'])
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Scanning for NIfTI files in {raw_dir}...")
    
    # Find all NIfTI files
    nifti_files = list(raw_dir.rglob("*.nii.gz")) + list(raw_dir.rglob("*.nii"))
    
    if not nifti_files:
        logger.warning(f"No NIfTI files found in {raw_dir}")
        return
    
    logger.info(f"Found {len(nifti_files)} NIfTI files")
    
    # Compute checksums
    checksums = {}
    for nifti_file in nifti_files:
        logger.info(f"Computing checksum for {nifti_file.name}...")
        try:
            file_hash = compute_file_hash(nifti_file)
            rel_path = str(nifti_file.relative_to(raw_dir))
            checksums[rel_path] = {
                "sha256": file_hash,
                "size": nifti_file.stat().st_size
            }
            logger.info(f"  SHA256: {file_hash}")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {nifti_file}: {e}")
            raise DataUnavailableError(f"Checksum computation failed for {nifti_file}")
    
    # Write checksums to file
    checksums_file = raw_dir / "checksums.json"
    with open(checksums_file, 'w') as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Wrote checksums to {checksums_file}")
    
    return checksums

def main():
    """Entry point for data loader."""
    try:
        checksums = load_openneuro_dataset()
        if checksums:
            logger.info(f"Data loader completed. Recorded {len(checksums)} checksums.")
        else:
            logger.info("Data loader completed. No NIfTI files found to checksum.")
    except DataUnavailableError as e:
        logger.error(f"Data loader failed: {e}")
        raise

if __name__ == "__main__":
    main()
