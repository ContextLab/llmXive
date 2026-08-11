"""
Profiling utilities for CPU/RAM and wall-clock time instrumentation.

This module provides standardized profiling functions to measure:
- Wall-clock time (latency) in milliseconds
- Peak RAM usage in megabytes

All profiling tasks in the project MUST use this module to ensure 
identical output keys for Gatekeeper and Baselines.
"""

import os
import time
import tracemalloc
import logging
import json
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager, List, NamedTuple
from contextlib import contextmanager

from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic function profiling
T = TypeVar('T')

class ProfileResult(NamedTuple):
    """Named tuple to hold profiling results."""
    latency_ms: float
    peak_ram_mb: float

# Global state for profiling
_profiling_active = False
_start_time: Optional[float] = None
_peak_memory: float = 0.0

def get_process_memory_mb() -> float:
    """
    Get current process memory usage in MB.
    
    Returns:
        Current memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        # If tracemalloc isn't active, try psutil as fallback
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            logger.warning("tracemalloc not active and psutil not available. Returning 0.0")
            return 0.0
    
    current, _ = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage since tracemalloc started in MB.
    
    Returns:
        Peak memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        # If tracemalloc isn't active, try psutil as fallback
        try:
            import psutil
            process = psutil.Process(os.getpid())
            # psutil doesn't track peak RSS easily, so we return current
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            logger.warning("tracemalloc not active and psutil not available. Returning 0.0")
            return 0.0
    
    _, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def start_profiling() -> None:
    """Start profiling with tracemalloc."""
    global _profiling_active, _start_time, _peak_memory
    
    if _profiling_active:
        logger.warning("Profiling already active. Resetting...")
        stop_profiling()
    
    tracemalloc.start()
    _start_time = time.perf_counter()
    _peak_memory = 0.0
    _profiling_active = True
    logger.debug("Profiling started")

def stop_profiling() -> ProfileResult:
    """
    Stop profiling and return results.
    
    Returns:
        ProfileResult with latency_ms and peak_ram_mb.
    """
    global _profiling_active, _start_time, _peak_memory
    
    if not _profiling_active:
        logger.warning("Profiling not active. Returning zero results.")
        return ProfileResult(latency_ms=0.0, peak_ram_mb=0.0)
    
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    
    latency_ms = (end_time - _start_time) * 1000.0
    peak_ram_mb = peak / (1024 * 1024)
    
    tracemalloc.stop()
    _profiling_active = False
    _start_time = None
    _peak_memory = peak_ram_mb
    
    logger.debug(f"Profiling stopped: {latency_ms:.2f}ms, {peak_ram_mb:.2f}MB peak")
    return ProfileResult(latency_ms=latency_ms, peak_ram_mb=peak_ram_mb)

def reset_profiling() -> None:
    """Reset profiling state without stopping tracemalloc."""
    global _start_time, _peak_memory
    
    if tracemalloc.is_tracing():
        tracemalloc.reset_peak()
    
    _start_time = time.perf_counter()
    _peak_memory = 0.0
    logger.debug("Profiling reset")

@contextmanager
def profile_block(label: str = "block") -> ContextManager[ProfileResult]:
    """
    Context manager for profiling a code block.
    
    Args:
        label: Label for logging purposes.
        
    Yields:
        ProfileResult with timing and memory info.
    """
    start_profiling()
    try:
        yield
    finally:
        result = stop_profiling()
        logger.info(f"Profile block '{label}': {result.latency_ms:.2f}ms, {result.peak_ram_mb:.2f}MB")

def profile_function(func: Callable[..., T]) -> Callable[..., Tuple[T, ProfileResult]]:
    """
    Decorator to profile a function's execution.
    
    Args:
        func: The function to profile.
        
    Returns:
        Wrapped function that returns (result, ProfileResult).
    """
    def wrapper(*args, **kwargs) -> Tuple[T, ProfileResult]:
        start_profiling()
        try:
            result = func(*args, **kwargs)
        finally:
            profile_result = stop_profiling()
            logger.info(
                f"Profile function '{func.__name__}': "
                f"{profile_result.latency_ms:.2f}ms, {profile_result.peak_ram_mb:.2f}MB"
            )
        return result, profile_result
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

def profile_execution(func: Callable[..., Any]) -> Callable[..., Dict[str, Any]]:
    """
    Profile a function's execution and return standardized results dict.
    
    This is the primary interface for profiling in the project.
    It ensures all profiling tasks return identical output keys:
    {'latency_ms': float, 'peak_ram_mb': float}
    
    Args:
        func: The function to profile.
        
    Returns:
        Wrapped function that returns a dict with standardized keys.
    """
    def wrapper(*args, **kwargs) -> Dict[str, Any]:
        start_profiling()
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise
        finally:
            profile_result = stop_profiling()
        
        # Return standardized dict as required by task specification
        return {
            'latency_ms': profile_result.latency_ms,
            'peak_ram_mb': profile_result.peak_ram_mb
        }
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

def get_results_summary(results: List[ProfileResult]) -> Dict[str, float]:
    """
    Calculate summary statistics from a list of profiling results.
    
    Args:
        results: List of ProfileResult objects.
        
    Returns:
        Dict with mean and std dev for latency and memory.
    """
    if not results:
        return {
            'mean_latency_ms': 0.0,
            'std_latency_ms': 0.0,
            'mean_peak_ram_mb': 0.0,
            'std_peak_ram_mb': 0.0
        }
    
    latencies = [r.latency_ms for r in results]
    memories = [r.peak_ram_mb for r in results]
    
    import numpy as np
    
    return {
        'mean_latency_ms': float(np.mean(latencies)),
        'std_latency_ms': float(np.std(latencies)),
        'mean_peak_ram_mb': float(np.mean(memories)),
        'std_peak_ram_mb': float(np.std(memories))
    }

def save_results_to_file(results: List[Dict[str, Any]], filepath: str) -> None:
    """
    Save profiling results to a JSON file.
    
    Args:
        results: List of result dicts with standardized keys.
        filepath: Path to output file.
    """
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved {len(results)} profiling results to {filepath}")

def main() -> None:
    """
    Main function for standalone testing of profiling utilities.
    
    Runs a simple benchmark and prints results.
    """
    logger.info("Running profiling utility test...")
    
    def dummy_work():
        """Simulate some work."""
        data = []
        for i in range(10000):
            data.append(i * i)
        return sum(data)
    
    # Profile the dummy work
    results = profile_execution(dummy_work)()
    
    print(f"Latency: {results['latency_ms']:.2f} ms")
    print(f"Peak RAM: {results['peak_ram_mb']:.2f} MB")
    
    # Test context manager
    with profile_block("test_block"):
        time.sleep(0.1)
    
    # Test decorator
    decorated_func = profile_function(dummy_work)
    _, profile_result = decorated_func()
    print(f"Decorated function: {profile_result.latency_ms:.2f}ms, {profile_result.peak_ram_mb:.2f}MB")
    
    # Test summary
    summary = get_results_summary([
        ProfileResult(100.0, 50.0),
        ProfileResult(120.0, 55.0),
        ProfileResult(90.0, 45.0)
    ])
    print(f"Summary: {summary}")

if __name__ == "__main__":
    # Setup logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
