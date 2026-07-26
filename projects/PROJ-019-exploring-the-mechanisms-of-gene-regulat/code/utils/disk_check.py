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
    Returns 0 if the path does not exist or an error occurs.
    """
    try:
        # Use os.statvfs for Unix-like systems and os.stat for Windows
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_free_bytes = ctypes.c_ulonglong(0)
            c_total_bytes = ctypes.c_ulonglong(0)
            c_total_free_bytes = ctypes.c_ulonglong(0)
            if kernel32.GetDiskFreeSpaceExW(
                str(path),
                ctypes.byref(c_free_bytes),
                ctypes.byref(c_total_bytes),
                ctypes.byref(c_total_free_bytes)
            ):
                return c_free_bytes.value
            return 0
        else:
            stat = os.statvfs(path)
            return stat.f_bavail * stat.f_frsize
    except Exception:
        return 0

def check_disk_space(path: Optional[Path] = None, min_space: int = MIN_DISK_SPACE_BYTES) -> None:
    """
    Check if there is sufficient disk space at the given path.
    Raises InsufficientDiskSpaceError if space is insufficient.
    """
    target_path = path or TMP_DIR
    available = get_available_space(target_path)

    if available < min_space:
        available_gb = available / (1024**3)
        required_gb = min_space / (1024**3)
        raise InsufficientDiskSpaceError(
            f"Insufficient disk space at {target_path}. "
            f"Available: {available_gb:.2f} GB, Required: {required_gb:.2f} GB."
        )

def main() -> None:
    """Entry point for CLI usage."""
    try:
        check_disk_space()
        print("Disk space check passed.")
    except InsufficientDiskSpaceError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
