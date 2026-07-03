"""
Disk space verification utilities.
"""
import os
import sys
from pathlib import Path
from typing import Optional
from code.config import TMP_DIR, MIN_DISK_SPACE_BYTES

class InsufficientDiskSpaceError(Exception):
    """Raised when available disk space is below the required threshold."""
    pass

def get_available_space(path: Path) -> int:
    """
    Get available disk space in bytes for the given path.
    
    Args:
        path: Directory path to check.
        
    Returns:
        Available space in bytes.
    """
    try:
        stat = os.statvfs(path)
        return stat.f_bavail * stat.f_frsize
    except FileNotFoundError:
        raise FileNotFoundError(f"Path does not exist: {path}")
    except PermissionError:
        raise PermissionError(f"Permission denied to access path: {path}")

def check_disk_space(path: Path = TMP_DIR, required_bytes: int = MIN_DISK_SPACE_BYTES) -> bool:
    """
    Check if there is sufficient disk space at the given path.
    
    Args:
        path: Directory path to check.
        required_bytes: Minimum required space in bytes.
        
    Returns:
        True if sufficient space is available.
        
    Raises:
        InsufficientDiskSpaceError: If insufficient space is available.
        FileNotFoundError: If path does not exist.
        PermissionError: If permission denied.
    """
    available = get_available_space(path)
    if available < required_bytes:
        raise InsufficientDiskSpaceError(
            f"Insufficient disk space at {path}: "
            f"{available / (1024**3):.2f}GB available, "
            f"{required_bytes / (1024**3):.2f}GB required."
        )
    return True

def main():
    """Main entry point for disk check script."""
    try:
        check_disk_space()
        print(f"Disk space check passed for {TMP_DIR}")
        return 0
    except (InsufficientDiskSpaceError, FileNotFoundError, PermissionError) as e:
        print(f"Disk space check failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
