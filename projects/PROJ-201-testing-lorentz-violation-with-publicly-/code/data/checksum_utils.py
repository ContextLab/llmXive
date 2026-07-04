"""
Utility functions for file integrity verification.
Used by downloader.py to verify checksums of downloaded CMB maps.
"""
import hashlib
from pathlib import Path
from typing import Optional

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify file integrity against expected hash.
    
    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected SHA-256 hash string.
        
    Returns:
        True if the hash matches.
        
    Raises:
        AssertionError: If the hash does not match.
        FileNotFoundError: If the file does not exist.
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found for checksum verification: {file_path}")
        
    file_hash = compute_sha256(file_path)
    if file_hash != expected_hash:
        raise AssertionError(
            f"Checksum mismatch for {file_path}: "
            f"expected {expected_hash}, got {file_hash}"
        )
    return True