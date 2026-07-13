import tracemalloc
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def start_profiling():
    """Start memory profiling."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        logger.info("Memory profiling started.")
    else:
        logger.warning("Memory profiling is already running.")

def stop_profiling() -> Optional[Tuple[float, float]]:
    """Stop memory profiling and return (current, peak) in bytes."""
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(f"Memory profiling stopped. Peak: {peak / (1024*1024):.2f} MB")
        return current, peak
    else:
        logger.warning("Memory profiling was not running.")
        return None

def get_current_memory_mb() -> float:
    """Get current memory usage in MB."""
    if tracemalloc.is_tracing():
        current, _ = tracemalloc.get_traced_memory()
        return current / (1024 * 1024)
    return 0.0

def get_peak_memory_mb() -> float:
    """Get peak memory usage in MB."""
    if tracemalloc.is_tracing():
        _, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    return 0.0

def check_memory_limit(limit_mb: float) -> bool:
    """Check if current memory usage is within the limit."""
    current = get_current_memory_mb()
    if current > limit_mb:
        logger.error(f"Memory limit exceeded: {current:.2f} MB > {limit_mb} MB")
        return False
    return True