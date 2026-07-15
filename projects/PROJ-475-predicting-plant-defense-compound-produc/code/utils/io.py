import hashlib
import os
from pathlib import Path
from typing import Union

class DiskSpaceError(Exception):
    """Raised when there is insufficient disk space."""
    pass

def compute_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
    
    Returns:
        Hexadecimal checksum string.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def check_disk_space(estimated_size: int) -> bool:
    """
    Check if there is enough disk space for the estimated size.
    Requires 1.5x the estimated size to be available.
    
    Args:
        estimated_size: Estimated size in bytes needed.
    
    Returns:
        True if sufficient space is available.
    
    Raises:
        DiskSpaceError: If available space is less than 1.5 * estimated_size.
    """
    # Get disk usage for the current directory (or a default path)
    # Using a generic path that should exist in the project root
    path = Path(".")
    if not path.exists():
        path = Path.home()
    
    try:
        stat = os.statvfs(path)
        available_bytes = stat.f_bavail * stat.f_frsize
        
        required_space = int(estimated_size * 1.5)
        
        if available_bytes < required_space:
            raise DiskSpaceError(
                f"Insufficient disk space. Required: {required_space} bytes, "
                f"Available: {available_bytes} bytes"
            )
        return True
    except OSError as e:
        raise DiskSpaceError(f"Could not check disk space: {e}")