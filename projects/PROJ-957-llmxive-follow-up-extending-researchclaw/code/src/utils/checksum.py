"""
SHA256 verification utilities for data artifacts.

Provides functions to compute, verify, write, and read SHA256 checksums
for ensuring data integrity in the llmXive research pipeline.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional


def compute_sha256(file_path: str | Path) -> str:
    """
    Compute the SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to compute checksum for.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def verify_checksum(file_path: str | Path, expected_checksum: str) -> bool:
    """
    Verify a file's SHA256 checksum against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA256 checksum (hex string).
        
    Returns:
        True if the computed checksum matches the expected checksum, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    computed = compute_sha256(file_path)
    return computed.lower() == expected_checksum.lower()


def write_checksum(file_path: str | Path, checksum: str, output_path: str | Path | None = None) -> Path:
    """
    Write a checksum to a file.
    
    If output_path is not specified, creates a .sha256 file alongside the original.
    
    Args:
        file_path: Path to the file whose checksum is being stored.
        checksum: The SHA256 checksum to write.
        output_path: Optional path for the checksum file. Defaults to <file>.sha256.
        
    Returns:
        Path to the created checksum file.
    """
    file_path = Path(file_path)
    if output_path is None:
        output_path = file_path.parent / f"{file_path.name}.sha256"
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    
    return output_path


def read_checksum(checksum_file_path: str | Path) -> Optional[str]:
    """
    Read a checksum from a .sha256 file.
    
    Expected format: "<checksum>  <filename>\n"
    
    Args:
        checksum_file_path: Path to the checksum file.
        
    Returns:
        The checksum string if found, None if the file doesn't exist or is empty.
        
    Raises:
        ValueError: If the checksum file format is invalid.
    """
    checksum_file_path = Path(checksum_file_path)
    
    if not checksum_file_path.exists():
        return None
    
    with open(checksum_file_path, "r", encoding="utf-8") as f:
        line = f.readline().strip()
    
    if not line:
        return None
    
    # Expected format: "<checksum>  <filename>"
    parts = line.split()
    if len(parts) < 1:
        raise ValueError(f"Invalid checksum file format: {checksum_file_path}")
    
    return parts[0].lower()

def verify_file_against_stored_checksum(file_path: str | Path, checksum_file_path: str | Path) -> bool:
    """
    Verify a file against a stored checksum file.
    
    Args:
        file_path: Path to the file to verify.
        checksum_file_path: Path to the .sha256 checksum file.
        
    Returns:
        True if verification passes, False otherwise.
        
    Raises:
        FileNotFoundError: If either file doesn't exist.
        ValueError: If the checksum file format is invalid.
    """
    file_path = Path(file_path)
    checksum_file_path = Path(checksum_file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not checksum_file_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file_path}")
    
    stored_checksum = read_checksum(checksum_file_path)
    if stored_checksum is None:
        raise ValueError(f"Could not read checksum from: {checksum_file_path}")
    
    return verify_checksum(file_path, stored_checksum)