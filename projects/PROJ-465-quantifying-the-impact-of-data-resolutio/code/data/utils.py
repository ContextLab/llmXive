"""
Data utility functions including checksum verification.
"""
import hashlib
import os
import logging
from pathlib import Path
from typing import Union, Optional
from code.utils.hash_artifact import compute_file_hash

logger = logging.getLogger(__name__)

def verify_checksum(file_path: Union[str, Path], checksum_file: Union[str, Path]) -> bool:
    """Verify a file's checksum against a stored checksum file."""
    if not os.path.exists(checksum_file):
        logger.warning(f"Checksum file not found: {checksum_file}")
        return False
    
    with open(checksum_file, 'r') as f:
        expected_hash = f.read().strip()
    
    actual_hash = compute_file_hash(file_path)
    
    if actual_hash == expected_hash:
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_hash}, Got: {actual_hash}")
        return False

def generate_checksum_file(file_path: Union[str, Path], output_path: Union[str, Path]):
    """Generate a checksum file for a given data file."""
    hash_val = compute_file_hash(file_path)
    with open(output_path, 'w') as f:
        f.write(hash_val)
    logger.info(f"Checksum generated for {file_path} -> {output_path}")
