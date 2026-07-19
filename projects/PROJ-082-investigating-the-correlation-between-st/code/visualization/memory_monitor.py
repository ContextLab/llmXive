import tracemalloc
import logging
import sys
from pathlib import Path
from typing import Callable, Any, Optional, Dict

from utils.logger import get_logger

# Default safe threshold: 256 MB (adjustable via env or parameter)
DEFAULT_MEMORY_THRESHOLD_MB = 256

def get_memory_threshold_mb() -> float:
    """Get memory threshold from environment or default."""
    import os
    try:
        return float(os.getenv("MEMORY_THRESHOLD_MB", DEFAULT_MEMORY_THRESHOLD_MB))
    except ValueError:
        return DEFAULT_MEMORY_THRESHOLD_MB

def monitor_memory(
    plot_name: str,
    threshold_mb: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> Callable:
    """
    Decorator to wrap plot generation functions with memory monitoring.
    
    Uses tracemalloc to track peak memory usage. If peak memory exceeds
    the threshold, raises a MemoryError with details about the plot
    causing the overflow.
    
    Args:
        plot_name: Name of the plot being generated (for logging)
        threshold_mb: Memory threshold in MB. If None, uses environment or default.
        logger: Logger instance. If None, creates a default one.
    
    Returns:
        Decorator function that wraps the target function.
    
    Raises:
        MemoryError: If peak memory usage exceeds the threshold.
    """
    if threshold_mb is None:
        threshold_mb = get_memory_threshold_mb()
    
    if logger is None:
        logger = get_logger("memory_monitor")
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            # Start tracking memory
            tracemalloc.start()
            
            try:
                # Execute the plot generation
                result = func(*args, **kwargs)
                
                # Get current and peak memory
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                peak_mb = peak / (1024 * 1024)
                
                logger.info(
                    f"Plot '{plot_name}' generated successfully. "
                    f"Peak memory: {peak_mb:.2f} MB (Threshold: {threshold_mb:.2f} MB)"
                )
                
                # Check if threshold exceeded
                if peak_mb > threshold_mb:
                    error_msg = (
                        f"Memory overflow detected for plot '{plot_name}': "
                        f"Peak memory {peak_mb:.2f} MB exceeds threshold {threshold_mb:.2f} MB. "
                        f"Aborting to prevent system instability."
                    )
                    logger.error(error_msg)
                    raise MemoryError(error_msg)
                
                return result
                
            except Exception as e:
                # Stop tracking on error
                tracemalloc.stop()
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator

def check_memory_usage(
    plot_name: str,
    threshold_mb: Optional[float] = None,
    logger: Optional[logging.Logger] = None
) -> bool:
    """
    Check current memory usage and log if it exceeds threshold.
    
    This is a non-decorator utility to manually check memory at a specific point.
    
    Args:
        plot_name: Name of the current operation/plot
        threshold_mb: Memory threshold in MB
        logger: Logger instance
    
    Returns:
        True if memory is within threshold, False otherwise.
    """
    if threshold_mb is None:
        threshold_mb = get_memory_threshold_mb()
    
    if logger is None:
        logger = get_logger("memory_monitor")
    
    current, peak = tracemalloc.get_traced_memory()
    peak_mb = peak / (1024 * 1024)
    
    if peak_mb > threshold_mb:
        logger.error(
            f"Memory threshold exceeded for '{plot_name}': "
            f"Peak {peak_mb:.2f} MB > Limit {threshold_mb:.2f} MB"
        )
        return False
    
    logger.debug(
        f"Memory check passed for '{plot_name}': "
        f"Peak {peak_mb:.2f} MB <= Limit {threshold_mb:.2f} MB"
    )
    return True

def log_memory_snapshot(
    plot_name: str,
    logger: Optional[logging.Logger] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Log a memory snapshot with top memory consumers.
    
    Args:
        plot_name: Name of the current operation
        logger: Logger instance
        limit: Number of top memory consumers to log
    
    Returns:
        Dictionary with memory statistics.
    """
    if logger is None:
        logger = get_logger("memory_monitor")
    
    current, peak = tracemalloc.get_traced_memory()
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')[:limit]
    
    stats = {
        "plot_name": plot_name,
        "current_mb": current / (1024 * 1024),
        "peak_mb": peak / (1024 * 1024),
        "top_allocations": []
    }
    
    for stat in top_stats:
        stats["top_allocations"].append({
            "file": str(stat.traceback),
            "size_mb": stat.size / (1024 * 1024),
            "count": stat.count
        })
    
    logger.info(f"Memory snapshot for '{plot_name}': {stats['peak_mb']:.2f} MB peak")
    return stats

def main():
    """
    Standalone test function to demonstrate memory monitoring.
    """
    logger = get_logger("memory_monitor")
    logger.info("Memory Monitor Module Test")
    
    # Start tracking
    tracemalloc.start()
    
    # Simulate some memory usage
    data = [i for i in range(1000000)]
    current, peak = tracemalloc.get_traced_memory()
    
    logger.info(f"Test allocation - Current: {current / 1024 / 1024:.2f} MB, Peak: {peak / 1024 / 1024:.2f} MB")
    
    tracemalloc.stop()
    
    logger.info("Memory Monitor module loaded successfully. Ready to wrap plot generation.")

if __name__ == "__main__":
    main()