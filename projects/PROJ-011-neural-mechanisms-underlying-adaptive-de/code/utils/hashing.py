"""
Hashing utilities for llmXive PROJ-011.
Computes SHA-256 checksums for data integrity verification.
"""
import hashlib
import os
from pathlib import Path
from typing import Union

from .io import ensure_dir, file_exists


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not file_exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def hash_directory_contents(dir_path: Union[str, Path], pattern: str = "*") -> dict:
    """
    Compute SHA-256 hashes for all files in a directory.
    
    Args:
        dir_path: Path to the directory.
        pattern: Glob pattern to match files (default: all files).
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
        
    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {path}")
    
    hashes = {}
    for file_path in path.rglob(pattern):
        if file_path.is_file():
            rel_path = file_path.relative_to(path)
            hashes[str(rel_path)] = compute_sha256(file_path)
    
    return hashes
