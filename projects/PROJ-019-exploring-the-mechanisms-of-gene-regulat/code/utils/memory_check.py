import os
import sys
from pathlib import Path
from typing import Optional
import psutil

# Minimum required RAM in bytes (16 GB)
MIN_RAM_BYTES = 16 * 1024 ** 3

class InsufficientMemoryError(Exception):
    """Raised when available memory is below the required threshold."""
    pass

def get_available_memory() -> int:
    """
    Get available system memory in bytes.
    
    Returns:
        Available memory in bytes
    """
    try:
        # Use psutil to get available memory
        mem = psutil.virtual_memory()
        return mem.available
    except Exception as e:
        # Fallback: try to read from /proc/meminfo on Linux
        if sys.platform.startswith('linux'):
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            key = parts[0].rstrip(':')
                            value = int(parts[1]) * 1024  # Convert KB to bytes
                            meminfo[key] = value
                    
                    # Available memory is typically MemAvailable
                    if 'MemAvailable' in meminfo:
                        return meminfo['MemAvailable']
                    elif 'MemFree' in meminfo and 'Buffers' in meminfo and 'Cached' in meminfo:
                        return meminfo['MemFree'] + meminfo['Buffers'] + meminfo['Cached']
            except Exception:
                pass
        
        # If we can't determine, raise an error
        raise InsufficientMemoryError("Unable to determine available memory")

def check_memory(min_required: int = MIN_RAM_BYTES) -> bool:
    """
    Check if available memory meets the minimum requirement.
    
    Args:
        min_required: Minimum required memory in bytes (default: 16 GB)
    
    Returns:
        True if memory is sufficient
    
    Raises:
        InsufficientMemoryError: If available memory is below the threshold
    """
    available = get_available_memory()
    
    if available < min_required:
        raise InsufficientMemoryError(
            f"Insufficient memory: {available / (1024**3):.2f} GB available, "
            f"{min_required / (1024**3):.2f} GB required"
        )
    
    return True

def main():
    """
    Main entry point for memory check utility.
    """
    try:
        check_memory()
        print("Memory check passed.")
        return 0
    except InsufficientMemoryError as e:
        print(f"Memory check failed: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())