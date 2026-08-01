"""
Compute SHA-256 checksums for downloaded ADReSS dataset files and record them.

This module implements Task T012e: Record computed SHA-256 checksum in 
`data/raw/checksums.json` with filename and hash.

Dependencies:
  - T012: Download utility (fetches the files)
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

from config import get_path, ensure_dirs
from utils import get_logger

# Configure logger
logger = get_logger(__name__)

def compute_sha256(filepath: Path) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        filepath: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found for hashing: {filepath}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {filepath} for hashing: {e}")
        raise

def record_checksums(checksums_dir: Path, filenames: list) -> None:
    """
    Compute and record SHA-256 checksums for a list of files into a JSON file.
    
    This function iterates through the provided filenames, computes their SHA-256
    hashes, and saves the results to `data/raw/checksums.json`.
    
    Args:
        checksums_dir: Directory containing the files to hash (e.g., data/raw).
        filenames: List of filenames (strings) present in checksums_dir.
        
    Raises:
        FileNotFoundError: If any of the specified files are missing.
    """
    checksums = []
    
    logger.info(f"Computing checksums for {len(filenames)} files in {checksums_dir}")
    
    for filename in filenames:
        filepath = checksums_dir / filename
        try:
            file_hash = compute_sha256(filepath)
            checksum_entry = {
                "filename": filename,
                "sha256": file_hash
            }
            checksums.append(checksum_entry)
            logger.info(f"Recorded checksum for {filename}: {file_hash[:16]}...")
        except FileNotFoundError as e:
            logger.error(str(e))
            raise
        
    # Ensure output directory exists
    output_path = checksums_dir / "checksums.json"
    ensure_dirs(output_path)
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksums successfully recorded to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write checksums to {output_path}: {e}")
        raise

def main() -> None:
    """
    Entry point for Task T012e.
    
    Scans the data/raw directory for ADReSS dataset files (assumed to be .zip or .tar.gz
    based on typical download patterns) and records their checksums.
    """
    raw_dir = get_path("data_raw")
    
    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist. No files to checksum.")
        return

    # Identify target files. In the context of ADReSS download (T012), 
    # we expect zip files. We scan for .zip and .tar.gz files.
    target_files = [
        f.name for f in raw_dir.iterdir() 
        if f.is_file() and (f.suffix == '.zip' or f.suffix == '.gz' or f.name.endswith('.tar.gz'))
    ]

    if not target_files:
        logger.warning(f"No downloadable archive files found in {raw_dir}. Nothing to checksum.")
        # Create an empty checksum file to indicate completion state if no files found
        output_path = raw_dir / "checksums.json"
        ensure_dirs(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return

    record_checksums(raw_dir, target_files)

if __name__ == "__main__":
    main()