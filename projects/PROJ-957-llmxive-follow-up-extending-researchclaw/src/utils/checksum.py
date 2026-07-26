"""
Checksum Utilities

Provides functions for computing, writing, reading, and verifying SHA256 checksums.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional

def compute_sha256(file_path: str) -> str:
    """
    Computes the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def write_checksum(file_path: str, checksum: str) -> None:
    """
    Writes a checksum to a file in the format 'sha256: <hex_string>'.
    
    Args:
        file_path: Path where the checksum file will be written.
        checksum: The hex string of the checksum.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    content = f"sha256: {checksum}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def read_checksum(file_path: str) -> Optional[str]:
    """
    Reads a checksum from a file.
    
    Args:
        file_path: Path to the checksum file.
        
    Returns:
        The checksum hex string, or None if the file is missing or malformed.
    """
    path = Path(file_path)
    if not path.exists():
        return None
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.startswith("sha256: "):
                return content.split("sha256: ")[1]
            return None
    except Exception:
        return None

def verify_file_against_stored_checksum(file_path: str, checksum_file_path: str) -> bool:
    """
    Verifies a file against a stored checksum.
    
    Args:
        file_path: Path to the file to verify.
        checksum_file_path: Path to the file containing the expected checksum.
        
    Returns:
        True if the checksums match, False otherwise.
    """
    stored_checksum = read_checksum(checksum_file_path)
    if stored_checksum is None:
        raise FileNotFoundError(f"Checksum file not found or malformed: {checksum_file_path}")
    
    computed_checksum = compute_sha256(file_path)
    return computed_checksum == stored_checksum

def verify_checksum(checksum1: str, checksum2: str) -> bool:
    """
    Compares two checksum strings.
    
    Args:
        checksum1: First checksum.
        checksum2: Second checksum.
        
    Returns:
        True if they match.
    """
    return checksum1.lower() == checksum2.lower()