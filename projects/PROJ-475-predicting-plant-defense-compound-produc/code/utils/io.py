"""
I/O Utilities for the Pipeline.
"""

import hashlib
import os
from pathlib import Path
from typing import Union

class DiskSpaceError(Exception):
    """Raised when there is insufficient disk space."""
    pass

def compute_checksum(file_path: Union[str, Path]) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        str: Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_disk_space(estimated_size: int, path: Union[str, Path] = ".") -> bool:
    """
    Checks if there is enough disk space for the estimated size.
    
    Raises:
        DiskSpaceError: If available space < 1.5 * estimated_size.
        
    Args:
        estimated_size: Estimated size in bytes.
        path: Path to check disk space for.
        
    Returns:
        bool: True if sufficient space.
    """
    path = Path(path)
    # Get disk usage
    stat = os.statvfs(path)
    available_space = stat.f_bavail * stat.f_frsize
    
    required_space = estimated_size * 1.5
    
    if available_space < required_space:
        raise DiskSpaceError(
            f"Insufficient disk space. Available: {available_space} bytes, "
            f"Required: {required_space} bytes (1.5x estimated {estimated_size})."
        )
    
    return True
