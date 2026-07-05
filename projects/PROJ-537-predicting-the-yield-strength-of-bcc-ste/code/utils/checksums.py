"""
Checksum utilities for data provenance tracking.

Generates and verifies SHA-256 checksums for data artifacts.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List

from .logging import get_logger

logger = get_logger(__name__)

def generate_checksum(file_path: Path) -> str:
    """
    Generate SHA-256 checksum for a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error generating checksum for {file_path}: {e}")
        raise

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify file checksum against expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA-256 hash
        
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = generate_checksum(file_path)
    return actual_checksum == expected_checksum

def generate_all_checksums(data_dir: Path = None) -> Dict[str, str]:
    """
    Generate checksums for all files in the data directory.
    
    Args:
        data_dir: Directory to scan (defaults to PROJECT_ROOT/data)
        
    Returns:
        Dictionary mapping relative file paths to checksums
    """
    from config import DATA_DIR
    
    if data_dir is None:
        data_dir = DATA_DIR
    
    checksums = {}
    
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(data_dir)
            checksum = generate_checksum(file_path)
            checksums[str(rel_path)] = checksum
            logger.debug(f"Generated checksum for {rel_path}: {checksum[:16]}...")
    
    return checksums