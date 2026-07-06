"""
Memory monitoring utilities for the llmXive pipeline.

Implements FR-011: Monitor RAM usage, trigger garbage collection at >90% 
of 6GB limit (5.4GB), and log warnings before critical thresholds.
"""
import gc
import logging
import os
import sys
import resource
from pathlib import Path
from typing import Optional, Tuple

# Constants for memory management
# 6GB limit as per FR-011
MEMORY_LIMIT_GB = 6.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3

# Thresholds
WARNING_THRESHOLD_PERCENT = 0.85  # 85% of 6GB = 5.1GB
CRITICAL_THRESHOLD_PERCENT = 0.90  # 90% of 6GB = 5.4GB
DANGEROUS_THRESHOLD_PERCENT = 0.95  # 95% of 6GB = 5.7GB

# Convert to bytes
WARNING_THRESHOLD_BYTES = MEMORY_LIMIT_BYTES * WARNING_THRESHOLD_PERCENT
CRITICAL_THRESHOLD_BYTES = MEMORY_LIMIT_BYTES * CRITICAL_THRESHOLD_PERCENT
DANGEROUS_THRESHOLD_BYTES = MEMORY_LIMIT_BYTES * DANGEROUS_THRESHOLD_PERCENT

# Logger instance
_logger: Optional[logging.Logger] = None

def _get_logger() -> logging.Logger:
    """Get or create the memory monitoring logger."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger("memory_monitor")
        _logger.setLevel(logging.INFO)
        
        # Create handler for pipeline_log.txt if it doesn't exist or is empty
        log_path = Path("pipeline_log.txt")
        if not _logger.handlers:
            handler = logging.FileHandler(log_path)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
    return _logger

def setup_memory_monitoring(log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize memory monitoring logging.
    
    Args:
        log_file: Optional path to log file. Defaults to 'pipeline_log.txt'.
        
    Returns:
        Configured logger instance.
    """
    global _logger
    logger = _get_logger()
    
    if log_file:
        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    logger.info(f"Memory monitoring initialized. Limit: {MEMORY_LIMIT_GB}GB")
    logger.info(f"Warning threshold: {WARNING_THRESHOLD_PERCENT*100:.0f}% ({WARNING_THRESHOLD_BYTES/1024**3:.2f}GB)")
    logger.info(f"Critical threshold: {CRITICAL_THRESHOLD_PERCENT*100:.0f}% ({CRITICAL_THRESHOLD_BYTES/1024**3:.2f}GB)")
    
    return logger

def get_memory_usage_bytes() -> int:
    """
    Get current memory usage in bytes.
    
    Uses resource.getrusage for Unix-like systems and psutil if available
    for cross-platform compatibility.
    
    Returns:
        Current memory usage in bytes.
    """
    try:
        # Try Unix/Linux/macOS using resource module
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # maxrss is in kilobytes on Linux/macOS, bytes on some systems
        # On Linux/macOS, convert from KB to bytes
        return usage.ru_maxrss * 1024
    except (ImportError, AttributeError):
        # Fallback for Windows or if resource doesn't work as expected
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            # Last resort: return 0 if nothing available
            logging.warning("Could not determine memory usage: neither resource nor psutil available")
            return 0

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in gigabytes.
    
    Returns:
        Current memory usage in GB.
    """
    bytes_usage = get_memory_usage_bytes()
    return bytes_usage / (1024**3)

def get_memory_percent() -> float:
    """
    Get current memory usage as a percentage of the 6GB limit.
    
    Returns:
        Memory usage percentage (0.0 to 1.0+).
    """
    bytes_usage = get_memory_usage_bytes()
    return bytes_usage / MEMORY_LIMIT_BYTES

def get_memory_stats() -> Tuple[float, float, float, float]:
    """
    Get comprehensive memory statistics.
    
    Returns:
        Tuple of (usage_gb, usage_percent, warning_threshold_gb, critical_threshold_gb)
    """
    usage_bytes = get_memory_usage_bytes()
    usage_gb = usage_bytes / (1024**3)
    usage_percent = usage_bytes / MEMORY_LIMIT_BYTES
    
    return (
        usage_gb,
        usage_percent,
        WARNING_THRESHOLD_BYTES / (1024**3),
        CRITICAL_THRESHOLD_BYTES / (1024**3)
    )

def check_memory_thresholds() -> Tuple[bool, bool, bool]:
    """
    Check current memory usage against defined thresholds.
    
    Returns:
        Tuple of (is_warning, is_critical, is_dangerous)
    """
    usage_percent = get_memory_percent()
    
    is_warning = usage_percent >= WARNING_THRESHOLD_PERCENT
    is_critical = usage_percent >= CRITICAL_THRESHOLD_PERCENT
    is_dangerous = usage_percent >= DANGEROUS_THRESHOLD_PERCENT
    
    return is_warning, is_critical, is_dangerous

def trigger_garbage_collection() -> int:
    """
    Trigger garbage collection and return the number of objects collected.
    
    Returns:
        Number of objects collected by the garbage collector.
    """
    collected = gc.collect()
    logger = _get_logger()
    logger.info(f"Garbage collection triggered. Collected {collected} objects.")
    return collected

def check_memory_checkpoint() -> bool:
    """
    Check memory usage and trigger GC if necessary.
    
    This function checks if memory usage exceeds the critical threshold (90%).
    If so, it triggers garbage collection and logs a warning.
    
    Returns:
        True if memory is within safe limits, False if critical.
    """
    logger = _get_logger()
    usage_gb, usage_percent, warn_gb, crit_gb = get_memory_stats()
    
    is_warning, is_critical, is_dangerous = check_memory_thresholds()
    
    if is_dangerous:
        logger.error(f"CRITICAL: Memory usage at {usage_percent*100:.1f}% ({usage_gb:.2f}GB). "
                   f"Approaching dangerous threshold ({DANGEROUS_THRESHOLD_PERCENT*100:.0f}%). "
                   f"Consider stopping the process.")
        return False
        
    if is_critical:
        logger.warning(f"CRITICAL THRESHOLD EXCEEDED: Memory usage at {usage_percent*100:.1f}% "
                     f"({usage_gb:.2f}GB). Triggering garbage collection.")
        trigger_garbage_collection()
        return False
        
    if is_warning:
        logger.warning(f"WARNING: Memory usage at {usage_percent*100:.1f}% "
                     f"({usage_gb:.2f}GB). Approaching critical threshold ({crit_gb:.2f}GB).")
        
    return True

def monitor_and_maybe_gc(threshold_percent: float = CRITICAL_THRESHOLD_PERCENT) -> bool:
    """
    Monitor memory and trigger garbage collection if threshold is exceeded.
    
    Args:
        threshold_percent: The threshold (0.0-1.0) at which to trigger GC.
                           Defaults to 90% (CRITICAL_THRESHOLD_PERCENT).
                           
    Returns:
        True if memory is safe, False if threshold was exceeded and GC was triggered.
    """
    logger = _get_logger()
    usage_percent = get_memory_percent()
    
    if usage_percent >= threshold_percent:
        logger.warning(
            f"Memory usage ({usage_percent*100:.1f}%) exceeded threshold "
            f"({threshold_percent*100:.1f}%). Triggering garbage collection."
        )
        trigger_garbage_collection()
        return False
        
    return True

def enforce_memory_limit() -> bool:
    """
    Enforce the memory limit by checking thresholds and triggering GC.
    
    This is the main entry point for memory management in long-running
    processes. It checks if memory usage exceeds the critical threshold (90%
    of 6GB = 5.4GB) and triggers garbage collection if necessary.
    
    Returns:
        True if memory is within safe limits, False if critical threshold
        was exceeded (after attempting GC).
    """
    logger = _get_logger()
    
    # Check current usage
    is_warning, is_critical, is_dangerous = check_memory_thresholds()
    
    if is_dangerous:
        logger.error(
            f"FATAL: Memory usage at {get_memory_percent()*100:.1f}% "
            f"({get_memory_usage_gb():.2f}GB). Exceeds dangerous threshold "
            f"({DANGEROUS_THRESHOLD_PERCENT*100:.0f}%). "
            f"Process may become unstable."
        )
        return False
        
    if is_critical:
        logger.warning(
            f"CRITICAL: Memory usage at {get_memory_percent()*100:.1f}% "
            f"({get_memory_usage_gb():.2f}GB). Exceeds critical threshold "
            f"({CRITICAL_THRESHOLD_PERCENT*100:.0f}%). Triggering garbage collection."
        )
        trigger_garbage_collection()
        
        # Re-check after GC
        is_warning, is_critical, is_dangerous = check_memory_thresholds()
        if is_critical or is_dangerous:
            logger.error(
                f"ERROR: Memory still critical after GC. Usage: "
                f"{get_memory_percent()*100:.1f}% ({get_memory_usage_gb():.2f}GB)."
            )
            return False
            
    elif is_warning:
        logger.warning(
            f"WARNING: Memory usage at {get_memory_percent()*100:.1f}% "
            f"({get_memory_usage_gb():.2f}GB). Approaching critical threshold."
        )
        
    return True

# Convenience function for use in loops
def checkpoint_memory(message: str = "") -> bool:
    """
    Checkpoint memory usage with an optional message.
    
    Args:
        message: Optional message to include in the log.
                
    Returns:
        True if memory is safe, False if critical.
    """
    logger = _get_logger()
    
    if message:
        logger.info(f"Memory checkpoint: {message}")
        
    return enforce_memory_limit()