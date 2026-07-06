"""
Memory monitoring utilities for the llmXive pipeline.

Provides functions to monitor RAM usage, trigger garbage collection
when memory usage exceeds 90% of the 6GB limit (5.4GB), and log
warnings before critical thresholds are reached.
"""
import gc
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Constants for memory management
MEMORY_LIMIT_GB = 6.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * (1024 ** 3)
WARNING_THRESHOLD_PERCENT = 0.90  # 90%
WARNING_THRESHOLD_BYTES = MEMORY_LIMIT_BYTES * WARNING_THRESHOLD_PERCENT
CRITICAL_THRESHOLD_PERCENT = 0.95  # 95%
CRITICAL_THRESHOLD_BYTES = MEMORY_LIMIT_BYTES * CRITICAL_THRESHOLD_PERCENT

# Global logger reference
_logger = None

def setup_memory_monitoring(logger: Optional[logging.Logger] = None) -> None:
    """
    Initialize the memory monitoring module with a logger.
    
    Args:
        logger: Optional logger instance. If not provided, uses the default
               'llmXive' logger from utils.py.
    """
    global _logger
    if logger is None:
        try:
            from utils import get_logger
            _logger = get_logger()
        except ImportError:
            _logger = logging.getLogger("llmXive.memory_utils")
            _logger.addHandler(logging.StreamHandler())
    else:
        _logger = logger

def get_memory_usage_bytes() -> int:
    """
    Get the current memory usage of the Python process in bytes.
    
    Returns:
        int: Memory usage in bytes. Returns 0 if the platform doesn't support
             memory reporting.
    """
    if sys.platform == "win32":
        # Windows: use psutil if available, else return 0
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return int(process.memory_info().rss)
        except ImportError:
            _logger.warning("psutil not available for memory monitoring on Windows. Returning 0.")
            return 0
    else:
        # Linux/Unix: read from /proc/self/status
        try:
            with open("/proc/self/status", "r") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        # VmRSS is in kB
                        parts = line.split()
                        if len(parts) >= 2:
                            return int(parts[1]) * 1024
        except (FileNotFoundError, ValueError, IndexError):
            pass
    
        # Fallback for macOS or if /proc is unavailable
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in bytes on macOS, kB on Linux
            if sys.platform == "darwin":
                return int(usage.ru_maxrss)
            else:
                return int(usage.ru_maxrss * 1024)
        except ImportError:
            pass
    
        _logger.warning("Could not determine memory usage on this platform.")
        return 0

def get_memory_usage_gb() -> float:
    """
    Get the current memory usage of the Python process in gigabytes.
    
    Returns:
        float: Memory usage in GB.
    """
    return get_memory_usage_bytes() / (1024 ** 3)

def get_memory_percent() -> float:
    """
    Get the current memory usage as a percentage of the 6GB limit.
    
    Returns:
        float: Percentage of memory used (0.0 to 100.0).
    """
    usage_bytes = get_memory_usage_bytes()
    if usage_bytes <= 0:
        return 0.0
    return (usage_bytes / MEMORY_LIMIT_BYTES) * 100.0

def get_memory_stats() -> Tuple[float, float, float, float]:
    """
    Get comprehensive memory statistics.
    
    Returns:
        Tuple containing:
            - current_usage_bytes (int)
            - current_usage_gb (float)
            - current_usage_percent (float)
            - remaining_bytes (int)
    """
    usage_bytes = get_memory_usage_bytes()
    usage_gb = usage_bytes / (1024 ** 3)
    usage_percent = (usage_bytes / MEMORY_LIMIT_BYTES) * 100.0
    remaining_bytes = int(MEMORY_LIMIT_BYTES - usage_bytes)
    
    return usage_bytes, usage_gb, usage_percent, remaining_bytes

def check_memory_thresholds() -> Tuple[bool, bool, str]:
    """
    Check if memory usage exceeds warning or critical thresholds.
    
    Returns:
        Tuple containing:
            - is_warning (bool): True if usage > 90%
            - is_critical (bool): True if usage > 95%
            - message (str): Status message describing the current state
    """
    usage_bytes = get_memory_usage_bytes()
    usage_percent = (usage_bytes / MEMORY_LIMIT_BYTES) * 100.0
    
    is_warning = usage_bytes > WARNING_THRESHOLD_BYTES
    is_critical = usage_bytes > CRITICAL_THRESHOLD_BYTES
    
    if is_critical:
        message = f"CRITICAL: Memory usage at {usage_percent:.1f}% ({usage_bytes / (1024**3):.2f} GB). Approaching 6GB limit."
    elif is_warning:
        message = f"WARNING: Memory usage at {usage_percent:.1f}% ({usage_bytes / (1024**3):.2f} GB). Exceeds 90% threshold."
    else:
        message = f"OK: Memory usage at {usage_percent:.1f}% ({usage_bytes / (1024**3):.2f} GB)."
    
    return is_warning, is_critical, message

def trigger_garbage_collection() -> int:
    """
    Trigger garbage collection and return the number of objects collected.
    
    Returns:
        int: Total number of objects collected across all generations.
    """
    if _logger:
        _logger.info("Triggering garbage collection...")
    
    collected = 0
    try:
        # Collect all generations
        for i in range(3):
            collected += gc.collect(i)
    except Exception as e:
        if _logger:
            _logger.error(f"Error during garbage collection: {e}")
    
    if _logger:
        _logger.info(f"Garbage collection complete. {collected} objects collected.")
    
    return collected

def check_memory_checkpoint() -> bool:
    """
    Check memory at a checkpoint. If >90% usage, trigger GC and re-check.
    If still >90% after GC, log warning.
    
    Returns:
        bool: True if memory is within acceptable limits (<90%), False otherwise.
    """
    usage_bytes = get_memory_usage_bytes()
    
    if usage_bytes > WARNING_THRESHOLD_BYTES:
        if _logger:
            _logger.warning(f"Memory checkpoint: {usage_bytes / (1024**3):.2f} GB used. Triggering GC.")
        
        trigger_garbage_collection()
        
        # Re-check after GC
        usage_bytes_after = get_memory_usage_bytes()
        usage_percent_after = (usage_bytes_after / MEMORY_LIMIT_BYTES) * 100.0
        
        if usage_bytes_after > WARNING_THRESHOLD_BYTES:
            if _logger:
                _logger.warning(f"Memory still high after GC: {usage_percent_after:.1f}% ({usage_bytes_after / (1024**3):.2f} GB).")
            return False
        else:
            if _logger:
                _logger.info(f"Memory reduced to {usage_percent_after:.1f}% after GC.")
            return True
    
    return True

def monitor_and_maybe_gc() -> bool:
    """
    Monitor memory usage and trigger GC if necessary.
    
    This function:
    1. Checks current memory usage
    2. If >90% of 6GB limit, triggers garbage collection
    3. Logs warnings if usage exceeds thresholds
    4. Returns True if usage is safe, False if critical
    
    Returns:
        bool: True if memory usage is below critical threshold, False otherwise.
    """
    is_warning, is_critical, message = check_memory_thresholds()
    
    if _logger:
        _logger.info(message)
    
    if is_critical:
        if _logger:
            _logger.error("CRITICAL memory level reached. Consider stopping the process.")
        return False
    
    if is_warning:
        trigger_garbage_collection()
        # Re-evaluate after GC
        is_warning_after, _, message_after = check_memory_thresholds()
        if _logger:
            _logger.info(f"After GC: {message_after}")
        if is_warning_after:
            # Still high, log warning but continue
            if _logger:
                _logger.warning("Memory usage remains high after garbage collection.")
            return True  # Still running, but high
    
    return True

def enforce_memory_limit(raise_on_limit: bool = True) -> bool:
    """
    Enforce the memory limit by checking current usage.
    
    Args:
        raise_on_limit: If True, raises a MemoryError if limit is exceeded.
                       If False, logs an error and returns False.
    
    Returns:
        bool: True if memory is within limits, False if exceeded.
    
    Raises:
        MemoryError: If raise_on_limit is True and memory exceeds the limit.
    """
    usage_bytes = get_memory_usage_bytes()
    usage_percent = (usage_bytes / MEMORY_LIMIT_BYTES) * 100.0
    
    if usage_bytes > MEMORY_LIMIT_BYTES:
        error_msg = f"Memory limit exceeded: {usage_percent:.1f}% ({usage_bytes / (1024**3):.2f} GB of {MEMORY_LIMIT_GB} GB)"
        if _logger:
            _logger.error(error_msg)
        
        if raise_on_limit:
            raise MemoryError(error_msg)
        return False
    
    return True