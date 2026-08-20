import tracemalloc
import resource
import sys
import json
import os
import gc
import logging
from typing import Optional, Callable, Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)

# Memory limits in MB
HARD_LIMIT_MB = 7000
WARNING_THRESHOLD_MB = 6500
BUFFER_MB = 500

_peak_rss_mb = 0.0
_monitoring_active = False

class MemoryLimitExceeded(Exception):
    """Raised when memory usage exceeds the defined hard limit."""
    pass

def reset_memory_tracker():
    """Reset the internal peak memory tracker."""
    global _peak_rss_mb
    _peak_rss_mb = 0.0
    logger.info("Memory tracker reset.")

def get_current_memory_mb() -> float:
    """
    Get the current Resident Set Size (RSS) of the process in MB.
    Uses resource module for accuracy on Unix-like systems, fallback to tracemalloc.
    """
    try:
        # resource module is more accurate for RSS
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, MB on macOS. Normalize to MB.
        maxrss_kb = usage.ru_maxrss
        # Detect OS to normalize units if necessary (Linux returns KB)
        if sys.platform != 'darwin':
            return maxrss_kb / 1024.0
        return float(maxrss_kb)
    except Exception:
        # Fallback to tracemalloc if resource is unavailable
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        return 0.0

def get_peak_memory_mb() -> float:
    """
    Get the peak RSS memory usage recorded so far in MB.
    Updates internal state with current reading if higher.
    """
    current = get_current_memory_mb()
    global _peak_rss_mb
    if current > _peak_rss_mb:
        _peak_rss_mb = current
    return _peak_rss_mb

def get_rss_memory_mb() -> float:
    """Alias for get_current_memory_mb for clarity in sweep loops."""
    return get_current_memory_mb()

def check_memory_limit(current_mb: Optional[float] = None) -> bool:
    """
    Check if current memory usage exceeds the HARD_LIMIT_MB.
    Returns True if limit is exceeded, False otherwise.
    """
    if current_mb is None:
        current_mb = get_current_memory_mb()
    return current_mb >= HARD_LIMIT_MB

def enforce_memory_limit(current_mb: Optional[float] = None) -> None:
    """
    Enforce memory limits with dynamic guardrails.
    
    Logic:
    1. If RSS >= HARD_LIMIT_MB (7GB): Raise MemoryLimitExceeded immediately.
    2. If RSS >= WARNING_THRESHOLD_MB (6.5GB): 
       - Pause processing.
       - Force garbage collection (gc.collect()).
       - Log a warning with the current RSS.
       - Resume processing.
    """
    if current_mb is None:
        current_mb = get_current_memory_mb()

    # Update peak tracking
    global _peak_rss_mb
    if current_mb > _peak_rss_mb:
        _peak_rss_mb = current_mb

    # Check Hard Limit (Fail Loudly)
    if current_mb >= HARD_LIMIT_MB:
        logger.error(f"CRITICAL: Memory limit exceeded. Current RSS: {current_mb:.2f}MB >= {HARD_LIMIT_MB}MB.")
        raise MemoryLimitExceeded(f"Memory limit exceeded: {current_mb:.2f}MB >= {HARD_LIMIT_MB}MB")

    # Check Warning Threshold (Dynamic Guardrail)
    if current_mb >= WARNING_THRESHOLD_MB:
        warning_msg = (
            f"WARNING: Memory usage approaching limit. "
            f"Current RSS: {current_mb:.2f}MB >= {WARNING_THRESHOLD_MB}MB. "
            f"Triggering garbage collection..."
        )
        logger.warning(warning_msg)
        
        # Pause and Force Garbage Collection
        gc.collect()
        
        # Log post-GC status
        post_gc_mb = get_current_memory_mb()
        logger.info(f"Post-GC Memory: {post_gc_mb:.2f}MB")
        
        if post_gc_mb >= HARD_LIMIT_MB:
            logger.error(f"CRITICAL: Memory still exceeds limit after GC: {post_gc_mb:.2f}MB.")
            raise MemoryLimitExceeded(f"Memory limit exceeded after GC: {post_gc_mb:.2f}MB")
        
        logger.info("Memory guardrail: Garbage collection completed. Resuming processing.")

def get_memory_snapshot() -> Dict[str, Any]:
    """Get a snapshot of current memory state."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "current_mb": get_current_memory_mb(),
        "peak_mb": get_peak_memory_mb(),
        "hard_limit_mb": HARD_LIMIT_MB,
        "warning_threshold_mb": WARNING_THRESHOLD_MB
    }

def save_memory_profile(output_path: str = "data/processed/memory_profile.json"):
    """
    Save the current memory profile to a JSON file.
    Creates the directory if it doesn't exist.
    """
    snapshot = get_memory_snapshot()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Append to existing file if it exists, or create new
    records = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                content = f.read().strip()
                if content:
                    # Handle JSON Lines or single JSON object
                    for line in content.split('\n'):
                        if line.strip():
                            records.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning(f"Could not parse existing {output_path}, starting fresh.")
            records = []
    
    records.append(snapshot)
    
    with open(output_path, 'w') as f:
        for rec in records:
            f.write(json.dumps(rec) + '\n')
    
    logger.debug(f"Memory profile saved to {output_path}")

def memory_monitor(callback: Callable[[float], None]) -> Callable[[float], None]:
    """
    Decorator or wrapper to enforce memory checks at specific intervals.
    
    Args:
        callback: A function that takes current memory MB and performs the check.
    
    Returns:
        A wrapped function that checks memory before executing the callback logic.
    """
    def wrapper(current_mb: float):
        enforce_memory_limit(current_mb)
        return callback(current_mb)
    return wrapper

def start_monitoring():
    """Start tracemalloc if not already running."""
    global _monitoring_active
    if not _monitoring_active:
        tracemalloc.start()
        _monitoring_active = True
        logger.info("Memory monitoring started (tracemalloc).")

def stop_monitoring():
    """Stop tracemalloc and save final profile."""
    global _monitoring_active
    if _monitoring_active:
        tracemalloc.stop()
        _monitoring_active = False
        logger.info("Memory monitoring stopped.")
        # Ensure final profile is saved
        save_memory_profile()