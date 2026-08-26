"""
I/O utility functions for the plant defense compound prediction project.
"""

import hashlib
import os
from pathlib import Path
from typing import Union

class DiskSpaceError(Exception):
    """Exception raised when there is insufficient disk space."""
    pass

def compute_checksum(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_disk_space(estimated_size: int, buffer_factor: float = 1.5) -> bool:
    """
    Check if there is enough disk space for the estimated size.

    Args:
        estimated_size: Estimated size in bytes.
        buffer_factor: Safety buffer factor (default 1.5).

    Returns:
        True if sufficient space, raises DiskSpaceError otherwise.
    """
    path = Path(".")
    try:
        total, used, free = os.statvfs(str(path))
        available_bytes = free * total  # Available bytes

        required_bytes = int(estimated_size * buffer_factor)

        if available_bytes < required_bytes:
            available_gb = available_bytes / (1024**3)
            required_gb = required_bytes / (1024**3)
            raise DiskSpaceError(
                f"Insufficient disk space. Available: {available_gb:.2f} GB, "
                f"Required: {required_gb:.2f} GB"
            )

        return True
    except OSError as e:
        raise DiskSpaceError(f"Failed to check disk space: {e}")