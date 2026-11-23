"""
Memory monitoring utility.
"""
import os
import sys
import logging

logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """
    Get current memory usage in MB.
    
    Returns:
        Memory usage in MB
    """
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux
    except Exception:
        # Fallback for non-Unix systems
        return 0.0

def check_memory_limit(limit_mb: int = 2048):
    """
    Check if memory usage is within limit.
    
    Args:
        limit_mb: Maximum allowed memory in MB
        
    Raises:
        MemoryError: If limit exceeded
    """
    current = get_memory_usage_mb()
    if current > limit_mb:
        raise MemoryError(f"Memory usage {current:.2f}MB exceeds limit {limit_mb}MB")
    logger.debug(f"Memory check passed: {current:.2f}MB / {limit_mb}MB")
