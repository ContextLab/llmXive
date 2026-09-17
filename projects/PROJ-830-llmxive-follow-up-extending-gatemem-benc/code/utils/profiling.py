"""
Profiling utilities for CPU/RAM and wall-clock time instrumentation.

This module provides standardized profiling functions to measure execution
latency and peak memory usage across the Gatekeeper and Baseline pipelines.

All profiling tasks MUST use the `profile_execution` function to ensure
identical output keys for consistent comparison.
"""

import os
import time
import tracemalloc
import logging
import json
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager, List, NamedTuple
from dataclasses import dataclass, field

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ProfileResult:
    """Standardized container for profiling results."""
    latency_ms: float
    peak_ram_mb: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary with standardized keys."""
        return {
            'latency_ms': self.latency_ms,
            'peak_ram_mb': self.peak_ram_mb
        }

def get_process_memory_mb() -> float:
    """
    Get current memory usage of the process in MB.
    
    Returns:
        float: Current memory usage in megabytes.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        # Fallback to tracemalloc if psutil is not available
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        current, peak = tracemalloc.get_traced_memory()
        return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage of the process in MB since tracing started.
    
    Returns:
        float: Peak memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

class ProfileContext(ContextManager['ProfileContext']):
    """
    Context manager for profiling a code block.
    
    Usage:
        with ProfileContext() as ctx:
            # code to profile
            result = ctx.get_result()
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory: float = 0.0
        self.start_memory: float = 0.0
    
    def __enter__(self) -> 'ProfileContext':
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        else:
            # Reset tracemalloc to get fresh peak for this block
            tracemalloc.clear_traces()
            tracemalloc.start()
        
        self.start_time = time.perf_counter()
        self.start_memory = get_process_memory_mb()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.end_time = time.perf_counter()
        self.peak_memory = get_peak_memory_mb()
        
        # Log profiling results
        if self.end_time and self.start_time:
            latency_ms = (self.end_time - self.start_time) * 1000
            logger.debug(f"ProfileContext: Latency={latency_ms:.2f}ms, Peak RAM={self.peak_memory:.2f}MB")
    
    def get_result(self) -> ProfileResult:
        """
        Get the profiling result.
        
        Returns:
            ProfileResult: Object containing latency and peak memory.
        """
        if not self.start_time or not self.end_time:
            raise RuntimeError("Context manager not properly exited")
        
        latency_ms = (self.end_time - self.start_time) * 1000
        return ProfileResult(latency_ms=latency_ms, peak_ram_mb=self.peak_memory)

def start_profiling() -> None:
    """Start global memory profiling."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        logger.info("Tracemalloc profiling started")

def stop_profiling() -> None:
    """Stop global memory profiling."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
        logger.info("Tracemalloc profiling stopped")

def reset_profiling() -> None:
    """Reset global memory profiling."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    tracemalloc.start()
    logger.info("Tracemalloc profiling reset")

def profile_block(block_name: str) -> Callable:
    """
    Decorator to profile a function's execution time and memory usage.
    
    Args:
        block_name: Name of the block for logging purposes.
    
    Returns:
        Decorated function that returns (result, profile_result).
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> tuple:
            with ProfileContext() as ctx:
                result = func(*args, **kwargs)
            profile_result = ctx.get_result()
            logger.info(f"ProfileBlock [{block_name}]: Latency={profile_result.latency_ms:.2f}ms, Peak RAM={profile_result.peak_ram_mb:.2f}MB")
            return result, profile_result
        return wrapper
    return decorator

def profile_execution(func: Optional[Callable] = None, *args, **kwargs) -> Dict[str, float]:
    """
    Profile the execution of a function or code block.
    
    This is the standardized function used across all profiling tasks
    to ensure identical output keys for Gatekeeper and Baselines.
    
    Args:
        func: Optional function to profile. If None, returns a context manager.
        *args: Arguments to pass to the function if provided.
        **kwargs: Keyword arguments to pass to the function if provided.
    
    Returns:
        Dict[str, float]: Dictionary with standardized keys:
            - 'latency_ms': Wall-clock time in milliseconds
            - 'peak_ram_mb': Peak RAM usage in megabytes
    
    Examples:
        # Profile a function call
        result = profile_execution(my_function, arg1, arg2=value)
        
        # Use as context manager
        with profile_execution() as ctx:
            my_function()
            result = ctx.get_result()
    """
    # If called as a context manager (no function provided)
    if func is None:
        return ProfileContext()
    
    # Profile the function execution
    with ProfileContext() as ctx:
        result = func(*args, **kwargs)
    
    profile_result = ctx.get_result()
    return profile_result.to_dict()

def get_results_summary(results_list: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Calculate summary statistics from a list of profiling results.
    
    Args:
        results_list: List of profiling result dictionaries.
    
    Returns:
        Dict[str, float]: Summary statistics including mean, std, min, max.
    """
    if not results_list:
        return {
            'mean_latency_ms': 0.0,
            'std_latency_ms': 0.0,
            'min_latency_ms': 0.0,
            'max_latency_ms': 0.0,
            'mean_peak_ram_mb': 0.0,
            'std_peak_ram_mb': 0.0,
            'min_peak_ram_mb': 0.0,
            'max_peak_ram_mb': 0.0
        }
    
    latencies = [r['latency_ms'] for r in results_list]
    rams = [r['peak_ram_mb'] for r in results_list]
    
    import numpy as np
    
    return {
        'mean_latency_ms': float(np.mean(latencies)),
        'std_latency_ms': float(np.std(latencies)),
        'min_latency_ms': float(np.min(latencies)),
        'max_latency_ms': float(np.max(latencies)),
        'mean_peak_ram_mb': float(np.mean(rams)),
        'std_peak_ram_mb': float(np.std(rams)),
        'min_peak_ram_mb': float(np.min(rams)),
        'max_peak_ram_mb': float(np.max(rams))
    }

def save_results_to_file(results: Dict[str, Any], filepath: str) -> None:
    """
    Save profiling results to a JSON file.
    
    Args:
        results: Dictionary of profiling results to save.
        filepath: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Profiling results saved to {filepath}")

def main():
    """Main function for standalone testing of profiling module."""
    logging.basicConfig(level=logging.INFO)
    
    # Test profile_execution with a simple function
    def sample_function():
        time.sleep(0.1)
        return "done"
    
    print("Testing profile_execution...")
    result = profile_execution(sample_function)
    print(f"Result: {result}")
    assert 'latency_ms' in result
    assert 'peak_ram_mb' in result
    assert isinstance(result['latency_ms'], float)
    assert isinstance(result['peak_ram_mb'], float)
    print("All tests passed!")

if __name__ == "__main__":
    main()
