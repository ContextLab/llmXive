"""
Configuration module for the robustness of statistical tests project.
Provides centralized access to random seed and memory constraints.
"""

import os
import sys
from typing import Optional

# Fixed random seed for reproducibility across all experiments
_SEED: int = 42

# Memory limit in bytes (default: 4GB to be safe on free-tier runners)
# Can be overridden via environment variable MEMORY_LIMIT_BYTES
_MEMORY_LIMIT_BYTES: int = int(os.environ.get("MEMORY_LIMIT_BYTES", 4 * 1024**3))


def get_seed() -> int:
    """
    Returns the fixed random seed used for all experiments.
    
    Returns:
        int: The random seed (default 42).
    """
    return _SEED


def check_memory_limit() -> bool:
    """
    Checks if the current process is within the memory limit.
    
    On Linux, reads /proc/self/status to get VmRSS (resident set size).
    On other platforms, attempts to use resource module if available,
    otherwise returns True (assuming no hard limit enforcement needed).
    
    Returns:
        bool: True if memory usage is within limit, False otherwise.
    """
    # Try Linux-specific method first
    if sys.platform == "linux":
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # Format: "VmRSS:    12345 kB"
                        parts = line.split()
                        if len(parts) >= 2:
                            rss_kb = int(parts[1])
                            rss_bytes = rss_kb * 1024
                            return rss_bytes <= _MEMORY_LIMIT_BYTES
        except (IOError, ValueError):
            pass  # Fallback to True if we can't read it

    # Try cross-platform method using resource (Unix-like)
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux/macOS, but units vary by platform
        # On Linux: KB, macOS: KB, Windows: not supported
        maxrss_kb = usage.ru_maxrss
        if sys.platform == "darwin":
            # macOS reports in KB
            maxrss_bytes = maxrss_kb * 1024
        else:
            # Assume KB for other Unix-like systems
            maxrss_bytes = maxrss_kb * 1024
        return maxrss_bytes <= _MEMORY_LIMIT_BYTES
    except ImportError:
        pass  # resource module not available (e.g., Windows)

    # If we can't determine, assume we're within limits
    return True


def set_memory_limit(bytes_limit: int) -> None:
    """
    Sets the memory limit for the current session.
    
    Args:
        bytes_limit: The new memory limit in bytes.
    """
    global _MEMORY_LIMIT_BYTES
    _MEMORY_LIMIT_BYTES = bytes_limit


def get_memory_limit() -> int:
    """
    Returns the current memory limit in bytes.
    
    Returns:
        int: The memory limit in bytes.
    """
    return _MEMORY_LIMIT_BYTES
