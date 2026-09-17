"""
Profiling utilities for CPU/RAM and wall-clock time instrumentation.

Provides standardized profiling functions to measure execution latency and
peak memory usage across Gatekeeper and Baseline pipelines.
"""

import os
import time
import tracemalloc
import logging
import json
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager, List, NamedTuple
from contextlib import contextmanager
from dataclasses import dataclass, asdict

from code.logging_config import setup_logging

# Initialize logger
logger = setup_logging(__name__)

@dataclass
class ProfileResult:
    """Container for profiling results."""
    latency_ms: float
    peak_ram_mb: float
    function_name: Optional[str] = None
    timestamp: Optional[str] = None

def get_process_memory_mb() -> float:
    """
    Get current memory usage of the process in MB.
    
    Returns:
        Current memory usage in megabytes.
    """
    try:
        # Try psutil first for more accurate process memory
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback to tracemalloc if psutil not available
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        else:
            # Last resort: /proc on Linux or approximate
            if os.name == 'posix':
                try:
                    with open('/proc/self/status', 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                return int(line.split()[1]) / 1024.0
                except (FileNotFoundError, ValueError, IndexError):
                    pass
            return 0.0

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage of the process in MB since tracing started.
    
    Returns:
        Peak memory usage in megabytes.
    """
    if tracemalloc.is_tracing():
        _, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    else:
        # If tracemalloc not tracing, return current memory as estimate
        logger.warning("tracemalloc not tracing. Returning current memory as peak estimate.")
        return get_process_memory_mb()

@contextmanager
def start_profiling():
    """
    Context manager to start profiling (tracemalloc and timer).
    
    Usage:
        with start_profiling() as profile_ctx:
            # code to profile
            result = profile_ctx.get_results()
    """
    tracemalloc.start()
    start_time = time.perf_counter()
    try:
        yield {'start_time': start_time}
    finally:
        pass

def stop_profiling(start_time: float) -> Dict[str, float]:
    """
    Stop profiling and return results.
    
    Args:
        start_time: The start time from start_profiling().
        
    Returns:
        Dictionary with 'latency_ms' and 'peak_ram_mb'.
    """
    end_time = time.perf_counter()
    latency_ms = (end_time - start_time) * 1000.0
    peak_ram_mb = get_peak_memory_mb()
    
    tracemalloc.stop()
    
    return {
        'latency_ms': latency_ms,
        'peak_ram_mb': peak_ram_mb
    }

def reset_profiling():
    """Reset tracemalloc by stopping and restarting."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    tracemalloc.start()

@contextmanager
def profile_block(label: str = "block") -> ContextManager[Dict[str, float]]:
    """
    Context manager to profile a specific code block.
    
    Args:
        label: Identifier for the profiled block.
        
    Yields:
        Dictionary with profiling results.
    """
    tracemalloc.start()
    start_time = time.perf_counter()
    try:
        yield {'label': label, 'start_time': start_time}
    finally:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000.0
        peak_ram_mb = get_peak_memory_mb()
        tracemalloc.stop()
        
        logger.info(f"Profile [{label}]: latency={latency_ms:.2f}ms, peak_ram={peak_ram_mb:.2f}MB")

def profile_function(func: Callable) -> Callable:
    """
    Decorator to profile a function's execution time and memory.
    
    Args:
        func: The function to profile.
        
    Returns:
        Wrapped function that profiles execution and returns results.
    """
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000.0
            peak_ram_mb = get_peak_memory_mb()
            tracemalloc.stop()
            
            logger.info(
                f"Profile [{func.__name__}]: latency={latency_ms:.2f}ms, "
                f"peak_ram={peak_ram_mb:.2f}MB"
            )
            
            # Attach profiling info to result if it's a dict
            if isinstance(result, dict):
                result['latency_ms'] = latency_ms
                result['peak_ram_mb'] = peak_ram_mb
            elif hasattr(result, '__dict__'):
                result.latency_ms = latency_ms
                result.peak_ram_mb = peak_ram_mb
            
            return result
    
    return wrapper

def profile_execution(func: Callable, *args, **kwargs) -> Dict[str, float]:
    """
    Profile a function execution and return standardized results.
    
    This is the primary standardized profiling interface for all tasks.
    It returns a dict with exactly these keys: {'latency_ms', 'peak_ram_mb'}.
    
    Args:
        func: The function to profile.
        *args: Positional arguments to pass to func.
        **kwargs: Keyword arguments to pass to func.
        
    Returns:
        Dictionary with standardized profiling keys.
    """
    tracemalloc.start()
    start_time = time.perf_counter()
    
    try:
        result = func(*args, **kwargs)
    finally:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000.0
        peak_ram_mb = get_peak_memory_mb()
        tracemalloc.stop()
    
    # Log the results
    logger.info(
        f"Execution profile for {func.__name__}: "
        f"latency_ms={latency_ms:.2f}, peak_ram_mb={peak_ram_mb:.2f}"
    )
    
    return {
        'latency_ms': float(latency_ms),
        'peak_ram_mb': float(peak_ram_mb)
    }

def get_results_summary(results_list: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Calculate summary statistics from a list of profiling results.
    
    Args:
        results_list: List of dicts with 'latency_ms' and 'peak_ram_mb'.
        
    Returns:
        Dictionary with mean, std, min, max for each metric.
    """
    import numpy as np
    
    if not results_list:
        return {
            'latency_ms_mean': 0.0,
            'latency_ms_std': 0.0,
            'latency_ms_min': 0.0,
            'latency_ms_max': 0.0,
            'peak_ram_mb_mean': 0.0,
            'peak_ram_mb_std': 0.0,
            'peak_ram_mb_min': 0.0,
            'peak_ram_mb_max': 0.0
        }
    
    latencies = [r['latency_ms'] for r in results_list]
    rams = [r['peak_ram_mb'] for r in results_list]
    
    return {
        'latency_ms_mean': float(np.mean(latencies)),
        'latency_ms_std': float(np.std(latencies)),
        'latency_ms_min': float(np.min(latencies)),
        'latency_ms_max': float(np.max(latencies)),
        'peak_ram_mb_mean': float(np.mean(rams)),
        'peak_ram_mb_std': float(np.std(rams)),
        'peak_ram_mb_min': float(np.min(rams)),
        'peak_ram_mb_max': float(np.max(rams))
    }

def save_results_to_file(results: Dict[str, Any], output_path: str):
    """
    Save profiling results to a JSON file.
    
    Args:
        results: Dictionary of results to save.
        output_path: Path to the output JSON file.
    """
    import json
    from pathlib import Path
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Profiling results saved to {output_path}")

def main():
    """
    Main function for testing the profiling module.
    Runs a simple benchmark to demonstrate functionality.
    """
    logger.info("Running profiling module self-test...")
    
    # Test function
    def sample_task():
        time.sleep(0.1)
        # Allocate some memory
        data = [i for i in range(100000)]
        return len(data)
    
    # Profile the task
    results = profile_execution(sample_task)
    
    print(f"Sample task results: {results}")
    
    # Verify structure
    assert 'latency_ms' in results, "Missing latency_ms key"
    assert 'peak_ram_mb' in results, "Missing peak_ram_mb key"
    assert isinstance(results['latency_ms'], float), "latency_ms must be float"
    assert isinstance(results['peak_ram_mb'], float), "peak_ram_mb must be float"
    assert results['latency_ms'] > 0, "latency_ms must be positive"
    assert results['peak_ram_mb'] >= 0, "peak_ram_mb must be non-negative"
    
    logger.info("Profiling module self-test passed.")
    return results

if __name__ == "__main__":
    main()
