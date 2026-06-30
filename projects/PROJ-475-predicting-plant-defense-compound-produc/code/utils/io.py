"""
Input/Output utilities for the plant defense compound prediction pipeline.

This module provides functions for file system interactions, checksum
computation, and disk space verification.
"""
import hashlib
import os
from pathlib import Path
from typing import Union

class DiskSpaceError(Exception):
    """Raised when available disk space is insufficient for an operation."""
    pass

def compute_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic checksum of a file.

    Args:
        file_path: Path to the file to be checksummed.
        algorithm: Hash algorithm to use ('sha256' or 'md5'). Default is 'sha256'.

    Returns:
        Hexadecimal string representation of the file's checksum.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm == "sha256":
        hasher = hashlib.sha256()
    elif algorithm == "md5":
        hasher = hashlib.md5()
    else:
        raise ValueError(f"Unsupported checksum algorithm: {algorithm}. Use 'sha256' or 'md5'.")

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

def check_disk_space(estimated_size: int, path: Union[str, Path] = ".") -> bool:
    """
    Check if there is sufficient disk space for an estimated file size.

    Requires at least 1.5x the estimated size to be available.

    Args:
        estimated_size: Estimated size of the file to be created (in bytes).
        path: Directory path to check space for. Defaults to current directory.

    Returns:
        True if sufficient space is available.

    Raises:
        DiskSpaceError: If available space is less than 1.5 * estimated_size.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    
    # Get absolute path to ensure correct stats
    path = path.resolve()
    
    try:
        statvfs = os.statvfs(path)
        # Available blocks * block size
        available_bytes = statvfs.f_frsize * statvfs.f_bavail
    except AttributeError:
        # Fallback for non-POSIX systems (though less precise)
        # This block is rarely reached in standard Python environments on Linux/Mac
        import shutil
        _, _, available_bytes = shutil.disk_usage(path)

    required_space = int(estimated_size * 1.5)

    if available_bytes < required_space:
        raise DiskSpaceError(
            f"Insufficient disk space. "
            f"Required: {required_space:,} bytes (1.5x {estimated_size:,}), "
            f"Available: {available_bytes:,} bytes."
        )
    
    return True