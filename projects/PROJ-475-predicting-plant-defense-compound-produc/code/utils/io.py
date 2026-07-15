"""
I/O utilities for the Plant Defense Compound Prediction Pipeline.

This module provides functions for file operations, checksum computation,
and disk space management.
"""
import hashlib
import os
from pathlib import Path
from typing import Union

class DiskSpaceError(Exception):
    """Exception raised when there is insufficient disk space."""
    pass

def compute_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of the SHA256 hash
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def check_disk_space(estimated_size: int, safety_factor: float = 1.5) -> bool:
    """
    Check if there is sufficient disk space for an operation.
    
    Args:
        estimated_size: Estimated size in bytes needed for the operation
        safety_factor: Safety factor to multiply estimated_size by (default 1.5)
        
    Returns:
        True if sufficient space is available
        
    Raises:
        DiskSpaceError: If insufficient disk space is available
    """
    # Get the project root directory (assuming this is called from code/utils/)
    project_root = Path(__file__).parent.parent.parent
    
    # Get disk usage statistics
    try:
        stat = os.statvfs(project_root)
        available_space = stat.f_bavail * stat.f_frsize
        required_space = int(estimated_size * safety_factor)
        
        if available_space < required_space:
            raise DiskSpaceError(
                f"Insufficient disk space. Available: {available_space / (1024**3):.2f} GB, "
                f"Required (with {safety_factor}x safety): {required_space / (1024**3):.2f} GB"
            )
        
        return True
    except Exception as e:
        # If we can't determine disk space, raise an error to be safe
        raise DiskSpaceError(f"Failed to check disk space: {e}")
