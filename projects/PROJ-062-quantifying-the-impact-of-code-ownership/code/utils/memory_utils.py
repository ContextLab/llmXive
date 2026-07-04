"""
Memory management utilities for the project.
Ensures peak RAM usage stays within 7 GB limit (FR-007).
"""

import gc
import os
import sys
import logging
from typing import Optional, Callable, Any
from pathlib import Path

from .logging_utils import get_logger

logger = get_logger(__name__)

# Memory limit in MB (7 GB)
MEMORY_LIMIT_MB = 7 * 1024

def get_current_memory_mb() -> float:
    """
    Get current memory usage in MB.
    
    Returns:
        Current memory usage in MB
    """
    try:
        import resource
        # Get memory usage of current process
        mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS, ru_maxrss is in bytes; on Linux, it's in KB
        if sys.platform == 'darwin':
            return mem / (1024 * 1024)
        else:
            return mem / 1024
    except ImportError:
        # Fallback for Windows or if resource module unavailable
        logger.warning("resource module not available, using psutil fallback")
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            logger.error("Neither resource nor psutil available for memory measurement")
            return 0.0

def check_memory_limit(limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """
    Check if current memory usage is within limit.
    
    Args:
        limit_mb: Memory limit in MB
    
    Returns:
        True if within limit, False otherwise
    """
    current = get_current_memory_mb()
    if current > limit_mb:
        logger.warning(f"Memory usage {current:.1f}MB exceeds limit {limit_mb:.1f}MB")
        return False
    return True

def force_gc() -> None:
    """Force garbage collection."""
    gc.collect()
    logger.debug("Forced garbage collection")

def clear_memory() -> None:
    """
    Clear memory by forcing GC and removing references.
    Should be called between repository processing iterations.
    """
    force_gc()
    logger.debug(f"Memory cleared. Current usage: {get_current_memory_mb():.1f}MB")

def process_repository_batch(func: Callable) -> Callable:
    """
    Decorator to process repositories with memory management.
    
    Ensures memory is cleared after each repository processing.
    
    Args:
        func: Function that processes a repository
    
    Returns:
        Wrapped function with memory management
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Clear memory after processing
            clear_memory()
            # Check if we're over limit
            if not check_memory_limit():
                logger.error("Memory limit exceeded after repository processing")
    
    return wrapper

# Import wraps here to avoid circular dependency
from functools import wraps

def memory_limit_decorator(limit_mb: float = MEMORY_LIMIT_MB) -> Callable:
    """
    Decorator to enforce memory limit on a function.
    
    Args:
        limit_mb: Memory limit in MB
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not check_memory_limit(limit_mb):
                raise MemoryError(f"Memory limit {limit_mb}MB exceeded before {func.__name__}")
            
            try:
                return func(*args, **kwargs)
            finally:
                clear_memory()
        return wrapper
    return decorator
