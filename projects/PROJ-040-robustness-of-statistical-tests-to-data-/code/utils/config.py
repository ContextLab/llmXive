import os
import sys
from typing import Optional

# Configuration constants
_SEED = 42
_MEMORY_LIMIT_MB = 7000  # 7 GB default for free-tier runners
_SAMPLE_FRACTION = 1.0   # Default: use full dataset

def get_seed() -> int:
    """
    Get the random seed for reproducibility.
    
    Returns:
        Random seed integer
    """
    return _SEED

def set_seed(seed: int) -> None:
    """
    Set the random seed.
    
    Args:
        seed: New seed value
    """
    global _SEED
    _SEED = seed

def get_memory_limit() -> int:
    """
    Get the memory limit in MB.
    
    Returns:
        Memory limit in MB
    """
    return _MEMORY_LIMIT_MB

def set_memory_limit(limit_mb: int) -> None:
    """
    Set the memory limit.
    
    Args:
        limit_mb: New limit in MB
    """
    global _MEMORY_LIMIT_MB
    _MEMORY_LIMIT_MB = limit_mb

def check_memory_limit() -> bool:
    """
    Check if current memory usage is within limits.
    
    Returns:
        True if within limit, False otherwise
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        current_mb = process.memory_info().rss / (1024 * 1024)
        return current_mb < _MEMORY_LIMIT_MB
    except ImportError:
        # psutil not available, assume OK
        return True
    except Exception:
        # Any error, assume OK to avoid crashing
        return True

def get_sample_fraction() -> float:
    """
    Get the fraction of data to sample if memory is constrained.
    
    Returns:
        Sample fraction (0.0 to 1.0)
    """
    return _SAMPLE_FRACTION

def set_sample_fraction(fraction: float) -> None:
    """
    Set the sample fraction.
    
    Args:
        fraction: New sample fraction
    """
    global _SAMPLE_FRACTION
    _SAMPLE_FRACTION = max(0.0, min(1.0, fraction))
