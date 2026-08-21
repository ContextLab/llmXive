import os
import time
import tracemalloc
import logging
import json
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager, List, NamedTuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ProfileResult(NamedTuple):
    """Standardized profiling result container."""
    latency_ms: float
    peak_ram_mb: float

# Global state for current profiling session
_start_time: Optional[float] = None
_tracemalloc_active: bool = False
_baseline_memory_mb: float = 0.0

def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        # Try psutil first (more accurate)
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback to tracemalloc if available
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        # Last resort: /proc on Linux
        try:
            with open(f'/proc/{os.getpid}/statm', 'r') as f:
                rss_pages = int(f.read().split()[1])
                page_size = os.sysconf('SC_PAGE_SIZE')
                return (rss_pages * page_size) / (1024 * 1024)
        except Exception:
            logger.warning("Could not determine memory usage")
            return 0.0

def get_peak_memory_mb() -> float:
    """Get peak memory usage since profiling started in MB."""
    if not _tracemalloc_active:
        return get_process_memory_mb()
    
    try:
        _, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    except Exception:
        logger.warning("tracemalloc not active or failed")
        return get_process_memory_mb()

def start_profiling():
    """Start profiling session (time + memory)."""
    global _start_time, _tracemalloc_active, _baseline_memory_mb
    
    _start_time = time.perf_counter()
    _baseline_memory_mb = get_process_memory_mb()
    
    if not _tracemalloc_active:
        tracemalloc.start()
        _tracemalloc_active = True
        logger.debug("tracemalloc started")

def stop_profiling() -> ProfileResult:
    """Stop profiling and return results."""
    global _start_time, _tracemalloc_active, _baseline_memory_mb
    
    if _start_time is None:
        raise RuntimeError("Profiling not started. Call start_profiling() first.")
    
    end_time = time.perf_counter()
    latency_ms = (end_time - _start_time) * 1000
    
    peak_memory = get_peak_memory_mb()
    
    # Reset state
    _start_time = None
    if _tracemalloc_active:
        tracemalloc.stop()
        _tracemalloc_active = False
    
    result = ProfileResult(latency_ms=latency_ms, peak_ram_mb=peak_memory)
    logger.info(f"Profiling complete: {latency_ms:.2f}ms, {peak_memory:.2f}MB peak")
    return result

def reset_profiling():
    """Reset profiling state without stopping tracemalloc."""
    global _start_time, _baseline_memory_mb
    _start_time = None
    _baseline_memory_mb = get_process_memory_mb()

@contextmanager
def profile_block(label: str = "block") -> ContextManager[ProfileResult]:
    """Context manager for profiling a code block."""
    start_profiling()
    try:
        yield
    finally:
        result = stop_profiling()
        logger.info(f"[{label}] {result.latency_ms:.2f}ms, {result.peak_ram_mb:.2f}MB")
        return result

def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function."""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_profiling()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profile_result = stop_profiling()
            logger.info(f"[{func.__name__}] {profile_result.latency_ms:.2f}ms, {profile_result.peak_ram_mb:.2f}MB")
    return wrapper

def profile_execution(func: Callable) -> Callable:
    """
    Profile a function's execution and return standardized dict.
    
    Returns a dict with keys: {'latency_ms': float, 'peak_ram_mb': float}
    This is the primary interface for Gatekeeper and Baselines to ensure
    identical output keys for profiling data.
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_profiling()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profile_result = stop_profiling()
            # Return standardized dict as required by task T007
            return {
                'latency_ms': float(profile_result.latency_ms),
                'peak_ram_mb': float(profile_result.peak_ram_mb)
            }
    return wrapper

def get_results_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate profiling results from multiple runs.
    
    Args:
        results: List of dicts with keys 'latency_ms' and 'peak_ram_mb'
    
    Returns:
        Dict with mean, std, min, max for each metric
    """
    if not results:
        return {}
    
    latencies = [r['latency_ms'] for r in results]
    memories = [r['peak_ram_mb'] for r in results]
    
    import statistics
    
    return {
        'latency_ms': {
            'mean': statistics.mean(latencies),
            'std': statistics.stdev(latencies) if len(latencies) > 1 else 0.0,
            'min': min(latencies),
            'max': max(latencies)
        },
        'peak_ram_mb': {
            'mean': statistics.mean(memories),
            'std': statistics.stdev(memories) if len(memories) > 1 else 0.0,
            'min': min(memories),
            'max': max(memories)
        }
    }

def save_results_to_file(results: List[Dict[str, Any]], output_path: str):
    """Save profiling results to a JSON file."""
    summary = get_results_summary(results)
    
    with open(output_path, 'w') as f:
        json.dump({
            'individual_results': results,
            'summary': summary
        }, f, indent=2)
    
    logger.info(f"Saved profiling results to {output_path}")

def main():
    """Demo/test function for profiling module."""
    logging.basicConfig(level=logging.INFO)
    
    def sample_function():
        time.sleep(0.1)
        return "done"
    
    logger.info("Running profiling demo...")
    start_profiling()
    result = sample_function()
    profile_result = stop_profiling()
    
    print(f"Function result: {result}")
    print(f"Latency: {profile_result.latency_ms:.2f}ms")
    print(f"Peak RAM: {profile_result.peak_ram_mb:.2f}MB")
    
    # Test decorator
    @profile_function
    def decorated_func():
        time.sleep(0.05)
        return "decorated"
    
    decorated_result = decorated_func()
    print(f"Decorated function result: {decorated_result}")

if __name__ == "__main__":
    main()
