"""
Memory monitoring utilities for the llmXive pipeline.

Provides functions to track RAM usage, enforce memory limits,
and trigger downsampling strategies when memory pressure is high.
"""
import os
import gc
import sys
import logging
import resource
from typing import Callable, List, Optional, Tuple, Any, Dict
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)

# Memory limit constant (6.5 GB in bytes)
MEMORY_LIMIT_GB = 6.5
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 ** 3

def get_memory_usage_bytes() -> int:
    """
    Get current memory usage of the Python process in bytes.
    
    Returns:
        int: Current memory usage in bytes.
    """
    if sys.platform == 'linux':
        try:
            # Read from /proc/self/statm
            with open('/proc/self/statm', 'r') as f:
                statm = f.read().split()
                # Second column is resident set size (RSS) in pages
                page_size = resource.getpagesize()
                return int(statm[1]) * page_size
        except (IOError, IndexError):
            # Fallback for other Linux-like systems
            pass
    
    # Fallback: use resource module (Unix-like systems)
    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux, bytes on macOS
        if sys.platform == 'darwin':
            return usage.ru_maxrss
        else:
            return usage.ru_maxrss * 1024
    except Exception:
        pass
    
    # Last resort: estimate based on gc
    try:
        # This is a rough estimate and not precise
        total = 0
        for obj in gc.get_objects():
            try:
                total += sys.getsizeof(obj)
            except (TypeError, AttributeError):
                continue
        return total
    except Exception:
        return 0

def get_memory_usage_gb() -> float:
    """
    Get current memory usage of the Python process in GB.
    
    Returns:
        float: Current memory usage in GB.
    """
    return get_memory_usage_bytes() / (1024 ** 3)

def check_memory_limit() -> bool:
    """
    Check if current memory usage exceeds the defined limit (6.5 GB).
    
    Returns:
        bool: True if memory usage is above limit, False otherwise.
    """
    current_usage = get_memory_usage_bytes()
    return current_usage >= MEMORY_LIMIT_BYTES

def force_gc() -> int:
    """
    Force garbage collection and return the number of objects collected.
    
    Returns:
        int: Number of objects collected.
    """
    collected = 0
    for gen in range(3):
        collected += gc.collect(gen)
    logger.info(f"Force GC collected {collected} objects.")
    return collected

class MemoryMonitor:
    """
    Context manager and utility class for monitoring memory usage
    and triggering downsampling when limits are exceeded.
    """
    
    def __init__(
        self,
        limit_gb: float = MEMORY_LIMIT_GB,
        downsampling_callback: Optional[Callable[[int], Any]] = None,
        log_interval_mb: float = 100.0
    ):
        """
        Initialize the memory monitor.
        
        Args:
            limit_gb: Memory limit in GB (default: 6.5 GB).
            downsampling_callback: Optional callback function to trigger downsampling.
                                   The callback should accept an integer argument 
                                   representing the target sample size.
            log_interval_mb: Log memory usage every N MB to avoid spam.
        """
        self.limit_bytes = limit_gb * 1024 ** 3
        self.downsampling_callback = downsampling_callback
        self.log_interval_bytes = log_interval_mb * 1024 ** 2
        self.last_logged_bytes = 0
        self.monitoring = False
        self._monitor_thread = None
        self._stop_monitoring = False

    def get_current_usage_gb(self) -> float:
        """Get current memory usage in GB."""
        return get_memory_usage_gb()

    def check_limit(self) -> bool:
        """
        Check if memory usage exceeds the limit.
        
        Returns:
            bool: True if limit exceeded.
        """
        return get_memory_usage_bytes() >= self.limit_bytes

    def trigger_downsample(self, current_size: int) -> int:
        """
        Trigger downsampling logic if callback is provided.
        
        Args:
            current_size: Current sample size.
            
        Returns:
            int: New sample size after downsampling.
        """
        if self.downsampling_callback:
            try:
                new_size = self.downsampling_callback(current_size)
                logger.info(f"Downsampling triggered: {current_size} -> {new_size}")
                return new_size
            except Exception as e:
                logger.error(f"Downsampling callback failed: {e}")
                # Return a conservative reduction
                return max(1, int(current_size * 0.5))
        else:
            logger.warning("Memory limit exceeded but no downsampling callback provided.")
            return current_size

    def log_usage(self):
        """Log memory usage if enough time has passed since last log."""
        current = get_memory_usage_bytes()
        if current - self.last_logged_bytes >= self.log_interval_bytes:
            logger.info(f"Memory usage: {current / (1024**3):.2f} GB / {self.limit_bytes / (1024**3):.2f} GB limit")
            self.last_logged_bytes = current

    def __enter__(self):
        self.monitoring = True
        logger.info("Memory monitoring started.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitoring = False
        logger.info("Memory monitoring stopped.")
        return False

def monitor_and_downsample(
    data_loader: Callable[[int], Tuple[Any, int]],
    initial_size: int,
    min_size: int = 100,
    reduction_factor: float = 0.7
) -> Tuple[Any, int]:
    """
    Monitor memory usage while loading data and trigger downsampling if limit is exceeded.
    
    Args:
        data_loader: A function that takes a sample size and returns (data, actual_size).
        initial_size: Starting sample size to attempt.
        min_size: Minimum allowed sample size.
        reduction_factor: Factor to reduce sample size when limit is exceeded.
        
    Returns:
        Tuple of (loaded_data, final_sample_size).
    """
    monitor = MemoryMonitor()
    current_size = initial_size
    
    while current_size >= min_size:
        logger.info(f"Attempting to load {current_size} samples...")
        try:
            data, actual_size = data_loader(current_size)
            
            # Check memory after loading
            if monitor.check_limit():
                logger.warning(f"Memory limit exceeded after loading {actual_size} samples.")
                force_gc()
                
                if current_size <= min_size:
                    logger.error(f"Cannot reduce further. Minimum size {min_size} reached but memory limit still exceeded.")
                    raise MemoryError(f"Memory limit exceeded even at minimum sample size {min_size}")
                
                # Reduce sample size
                new_size = max(min_size, int(current_size * reduction_factor))
                logger.info(f"Reducing sample size from {current_size} to {new_size}")
                current_size = new_size
                
                # Clean up previous data
                del data
                force_gc()
            else:
                logger.info(f"Successfully loaded {actual_size} samples within memory limit.")
                return data, actual_size
                
        except MemoryError as e:
            logger.warning(f"MemoryError during load: {e}")
            force_gc()
            new_size = max(min_size, int(current_size * reduction_factor))
            if new_size == current_size:
                logger.error("Unable to reduce sample size further.")
                raise
            current_size = new_size
    
    raise MemoryError(f"Failed to load data within memory limit even at minimum size {min_size}")

def get_downsample_signal(
    current_usage_gb: float,
    target_usage_gb: float = 5.5
) -> Optional[Dict[str, Any]]:
    """
    Generate a signal for downsampling based on current usage.
    
    Args:
        current_usage_gb: Current memory usage in GB.
        target_usage_gb: Target memory usage after downsampling.
        
    Returns:
        Dict with downsampling signal details, or None if not needed.
    """
    if current_usage_gb >= MEMORY_LIMIT_GB:
        reduction_needed = (current_usage_gb - target_usage_gb) / current_usage_gb
        return {
            "signal": "downsample",
            "current_gb": current_usage_gb,
            "target_gb": target_usage_gb,
            "reduction_factor": max(0.1, 1.0 - reduction_needed),
            "reason": "Memory usage exceeds 6.5 GB limit"
        }
    elif current_usage_gb >= 6.0:
        # Warning level
        return {
            "signal": "warning",
            "current_gb": current_usage_gb,
            "reason": "Memory usage approaching limit"
        }
    return None