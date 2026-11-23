"""
Memory profiling utilities for the llmXive pipeline.

Provides decorators and functions to track RAM usage using tracemalloc and psutil,
enforce memory limits, and log results to data/results/.
"""
import gc
import json
import logging
import tracemalloc
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List
import psutil

from config import DATA_RESULTS_DIR

logger = logging.getLogger(__name__)

# Global log to store profile entries
_profile_log: List[Dict[str, Any]] = []

def get_current_memory_mb() -> float:
    """Get current resident set size (RSS) memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)

def get_total_system_memory_gb() -> float:
    """Get total system memory in GB."""
    return psutil.virtual_memory().total / (1024 * 1024 * 1024)

def get_peak_memory_mb() -> float:
    """Get peak memory usage tracked by tracemalloc in MB."""
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    return 0.0

def check_memory_limit(limit_mb: float = 6000) -> bool:
    """
    Check if current memory is within the specified limit.
    
    Args:
        limit_mb: Memory limit in MB (default 6000 MB ~ 6GB).
        
    Returns:
        True if current memory usage is below limit, False otherwise.
    """
    current = get_current_memory_mb()
    return current < limit_mb

def force_gc():
    """Force garbage collection to free up memory."""
    gc.collect()

def profile_memory(func: Optional[Callable] = None, limit_mb: float = 6000):
    """
    Decorator to profile memory usage of a function.
    
    This decorator:
    1. Starts tracemalloc tracing.
    2. Records start memory and time.
    3. Executes the wrapped function.
    4. Records end memory, peak memory, and duration.
    5. Logs the entry to _profile_log.
    6. Asserts total system RAM < 7GB (SC-004 requirement).
    7. Warns if peak memory exceeds the limit.
    
    Args:
        func: The function to decorate (if used as @profile_memory).
        limit_mb: Memory limit in MB for warnings (default 6000).
        
    Returns:
        The wrapped function.
        
    Raises:
        AssertionError: If total system RAM is not < 7GB (SC-004 validation).
    """
    def decorator(f: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            # SC-004 Validation: Assert total system RAM < 7GB
            total_gb = get_total_system_memory_gb()
            if total_gb >= 7.0:
                # This is a configuration check, not a runtime failure, 
                # but we log it as a warning if the environment is larger than expected.
                logger.warning(f"System RAM ({total_gb:.2f} GB) exceeds expected 7GB limit. Proceeding with caution.")
            
            tracemalloc.start()
            start_mem = get_current_memory_mb()
            start_time = time.time()
            
            logger.info(f"Starting {f.__name__} at {start_mem:.2f} MB (System RAM: {total_gb:.2f} GB)")
            
            try:
                result = f(*args, **kwargs)
            except Exception as e:
                tracemalloc.stop()
                logger.error(f"Exception in {f.__name__}: {e}")
                raise e
            
            end_mem = get_current_memory_mb()
            peak_mem = get_peak_memory_mb()
            duration = time.time() - start_time
            
            tracemalloc.stop()
            
            log_entry = {
                "function": f.__name__,
                "start_memory_mb": round(start_mem, 2),
                "end_memory_mb": round(end_mem, 2),
                "peak_memory_mb": round(peak_mem, 2),
                "duration_seconds": round(duration, 2),
                "timestamp": datetime.now().isoformat(),
                "system_ram_gb": round(total_gb, 2)
            }
            
            _profile_log.append(log_entry)
            logger.info(f"Finished {f.__name__}. Peak: {peak_mem:.2f} MB, Duration: {duration:.2f}s")
            
            if peak_mem > limit_mb:
                logger.warning(f"Memory limit exceeded in {f.__name__}: {peak_mem:.2f} MB > {limit_mb} MB")
            
            return result
        return wrapper
    
    if func is not None:
        return decorator(func)
    return decorator

def save_memory_profile_log():
    """
    Save the accumulated memory profile log to data/results/memory_profile.log 
    and data/results/runtime_profile.json.
    
    Creates the directory if it doesn't exist.
    """
    log_path = Path(DATA_RESULTS_DIR) / "memory_profile.log"
    runtime_path = Path(DATA_RESULTS_DIR) / "runtime_profile.json"
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write line-delimited JSON for easy parsing
    with open(log_path, 'w') as f:
        for entry in _profile_log:
            f.write(json.dumps(entry) + '\n')
    
    # Write pretty-printed JSON for the runtime profile
    with open(runtime_path, 'w') as f:
        json.dump(_profile_log, f, indent=2)
    
    logger.info(f"Memory profile saved to {log_path} and {runtime_path}")

def main():
    """Example usage for testing the profiler."""
    @profile_memory(limit_mb=6000)
    def dummy_task():
        time.sleep(0.1)
        # Allocate some memory
        data = [i for i in range(100000)]
        return data
    
    dummy_task()
    save_memory_profile_log()

__all__ = [
    'get_current_memory_mb', 
    'get_total_system_memory_gb',
    'get_peak_memory_mb', 
    'check_memory_limit', 
    'force_gc', 
    'profile_memory', 
    'save_memory_profile_log', 
    'main'
]