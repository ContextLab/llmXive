import os
import sys
from typing import Optional

# Default configuration values
_SEED = 42
# Memory limit in MB (7GB default for free-tier runners)
_MEMORY_LIMIT_MB = 7000
# Percentage of dataset to use if memory is exceeded (0.0 to 1.0)
_MEMORY_SAMPLE_FRACTION = 0.5

def get_seed() -> int:
    """Return the fixed random seed for reproducibility."""
    return _SEED

def set_memory_limit(limit_mb: int) -> None:
    """Set the memory limit in megabytes."""
    global _MEMORY_LIMIT_MB
    _MEMORY_LIMIT_MB = limit_mb

def get_memory_limit() -> int:
    """Return the current memory limit in megabytes."""
    return _MEMORY_LIMIT_MB

def check_memory_limit() -> bool:
    """
    Check if the current estimated memory usage is within the limit.
    
    This function attempts to estimate available memory.
    Returns True if within limits, False otherwise.
    
    Note: On systems where memory info is unavailable, it returns True
    to avoid false positives, but logs a warning.
    """
    try:
        if sys.platform == "linux" or sys.platform == "linux2":
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            mem_total = 0
            mem_available = 0
            for line in lines:
                if line.startswith("MemTotal:"):
                    mem_total = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    mem_available = int(line.split()[1])
            
            # Convert kB to MB
            mem_available_mb = mem_available / 1024
            
            if mem_available_mb < _MEMORY_LIMIT_MB:
                return False
            return True
        
        elif sys.platform == "darwin":
            # macOS: use sysctl (simplified check)
            import subprocess
            try:
                result = subprocess.run(['sysctl', '-n', 'hw.memsize'], 
                                      capture_output=True, text=True, check=True)
                mem_bytes = int(result.stdout.strip())
                mem_mb = mem_bytes / (1024 * 1024)
                if mem_mb < _MEMORY_LIMIT_MB:
                    return False
                return True
            except (subprocess.CalledProcessError, ValueError):
                return True  # Fail safe
        
        else:
            # Windows or unknown: assume safe limit or try psutil if available
            try:
                import psutil
                mem = psutil.virtual_memory()
                if mem.available / (1024 * 1024) < _MEMORY_LIMIT_MB:
                    return False
                return True
            except ImportError:
                return True  # Fail safe if psutil not available
                
    except Exception:
        # If we can't check, assume safe to proceed
        return True

def get_sample_fraction() -> float:
    """Return the fraction of data to sample if memory limits are hit."""
    return _MEMORY_SAMPLE_FRACTION
