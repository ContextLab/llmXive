"""
Utility functions for computing checksums.
"""
import hashlib
import json
from pathlib import Path
from typing import Optional

from utils.logging import get_logger

logger = get_logger()

def compute_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time (for large files).
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def write_checksum_file(file_path: Path, checksum: str, output_path: Optional[Path] = None) -> Path:
    """
    Write a checksum to a .sha256 file.
    
    Args:
        file_path: The file the checksum belongs to (for naming context).
        checksum: The checksum string.
        output_path: Optional specific path for the checksum file. Defaults to file_path + ".sha256".
        
    Returns:
        Path to the written checksum file.
    """
    if output_path is None:
        output_path = file_path.with_suffix(file_path.suffix + ".sha256")
    
    with open(output_path, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    
    logger.info(f"Wrote checksum to {output_path}")
    return output_path

def generate_and_save_checksum(file_path: Path, output_path: Optional[Path] = None) -> str:
    """
    Compute checksum for a file and save it to disk.
    
    Args:
        file_path: Path to the file to hash.
        output_path: Optional path for the checksum file.
        
    Returns:
        The computed checksum string.
    """
    checksum = compute_sha256(file_path)
    write_checksum_file(file_path, checksum, output_path)
    return checksum
