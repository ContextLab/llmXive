"""
Checksum utilities for data integrity verification.

Provides functions to compute SHA-256 hashes and manage checksum records.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> Optional[str]:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash, or None if file not found
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None

def record_checksums(checksum_file: Path, records: list) -> None:
    """
    Save a list of checksum records to a JSON file.
    
    Args:
        checksum_file: Path to the output JSON file
        records: List of checksum record dictionaries
    """
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_file, 'w', encoding='utf-8') as f:
        json.dump({"checksums": records}, f, indent=2)
    logger.info(f"Saved {len(records)} checksum records to {checksum_file}")

def main():
    """
    Main entry point for checksum utilities.
    This is a placeholder for potential command-line usage.
    """
    logger.info("Checksum utilities module loaded")

if __name__ == "__main__":
    main()
