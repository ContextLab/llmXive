"""
Profiling utilities for CPU/RAM and wall-clock time instrumentation.

Provides standardized profiling functions to ensure consistent output keys
across Gatekeeper and Baseline executions.
"""
import os
import time
import tracemalloc
import logging
import json
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager, List, NamedTuple
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProfileResult:
    """Standardized result container for profiling execution."""
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
    Get current process memory usage in MB.
    
    Returns:
        float: Current memory usage in MB.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        logger.warning("psutil not available, using tracemalloc fallback")
        if tracemalloc.is_tracing():
            current, _ = tracemalloc.get_traced_memory()
            return current / (1024 * 1024)
        return 0.0

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage since tracemalloc started in MB.
    
    Returns:
        float: Peak memory usage in MB.
    """
    if tracemalloc.is_tracing():
        _, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024)
    return 0.0

def start_profiling() -> None:
    """Start memory and time profiling."""
    tracemalloc.start()
    logger.info("Profiling started")

def stop_profiling() -> None:
    """Stop memory profiling."""
    tracemalloc.stop()
    logger.info("Profiling stopped")

def reset_profiling() -> None:
    """Reset profiling state."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    tracemalloc.start()
    logger.info("Profiling reset")

class profile_block(ContextManager):
    """
    Context manager for profiling a code block.
    
    Usage:
        with profile_block() as result:
            # code to profile
            pass
        print(result.latency_ms, result.peak_ram_mb)
    """
    def __init__(self):
        self.start_time: Optional[float] = None
        self.result: Optional[ProfileResult] = None

    def __enter__(self) -> 'profile_block':
        self.start_time = time.perf_counter()
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        end_time = time.perf_counter()
        latency_ms = (end_time - self.start_time) * 1000
        peak_ram_mb = get_peak_memory_mb()
        self.result = ProfileResult(
            latency_ms=latency_ms,
            peak_ram_mb=peak_ram_mb
        )
        logger.debug(f"Block profiled: {latency_ms:.2f}ms, {peak_ram_mb:.2f}MB")

T = TypeVar('T')

def profile_function(func: Callable[..., T]) -> Callable[..., Tuple[T, ProfileResult]]:
    """
    Decorator to profile a function's execution time and memory usage.
    
    Args:
        func: Function to profile.
        
    Returns:
        Wrapped function that returns (result, profile_result).
    """
    def wrapper(*args, **kwargs) -> Tuple[T, ProfileResult]:
        with profile_block() as profile_result:
            result = func(*args, **kwargs)
        return result, profile_result.result
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

def profile_execution(func: Callable[..., Any]) -> ProfileResult:
    """
    Profile a function's execution and return standardized metrics.
    
    This is the primary entry point for profiling tasks to ensure
    identical output keys (latency_ms, peak_ram_mb) across all components.
    
    Args:
        func: Function to profile.
        
    Returns:
        ProfileResult with latency_ms and peak_ram_mb.
        
    Example:
        def my_function():
            time.sleep(0.1)
            return "done"
        
        result = profile_execution(my_function)
        print(result.latency_ms, result.peak_ram_mb)
    """
    with profile_block() as result:
        func()
    return result

def get_results_summary(results: List[ProfileResult]) -> Dict[str, Any]:
    """
    Calculate summary statistics from a list of profiling results.
    
    Args:
        results: List of ProfileResult objects.
        
    Returns:
        Dictionary with mean, std, min, max for latency and memory.
    """
    if not results:
        return {
            'latency_ms': {'mean': 0, 'std': 0, 'min': 0, 'max': 0},
            'peak_ram_mb': {'mean': 0, 'std': 0, 'min': 0, 'max': 0}
        }
    
    latencies = [r.latency_ms for r in results]
    memories = [r.peak_ram_mb for r in results]
    
    import numpy as np
    
    return {
        'latency_ms': {
            'mean': float(np.mean(latencies)),
            'std': float(np.std(latencies)),
            'min': float(np.min(latencies)),
            'max': float(np.max(latencies))
        },
        'peak_ram_mb': {
            'mean': float(np.mean(memories)),
            'std': float(np.std(memories)),
            'min': float(np.min(memories)),
            'max': float(np.max(memories))
        }
    }

def save_results_to_file(results: List[ProfileResult], filepath: str) -> None:
    """
    Save profiling results to a JSON file.
    
    Args:
        results: List of ProfileResult objects.
        filepath: Path to output file.
    """
    data = {
        'results': [r.to_dict() for r in results],
        'summary': get_results_summary(results)
    }
    
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved profiling results to {filepath}")

def main():
    """Demo and test of profiling functionality."""
    logger.info("Running profiling demo...")
    
    def sample_function():
        time.sleep(0.05)
        return "completed"
    
    result = profile_execution(sample_function)
    logger.info(f"Sample function profiled: {result.latency_ms:.2f}ms, {result.peak_ram_mb:.2f}MB")
    
    # Test with multiple runs
    results = []
    for i in range(3):
        r = profile_execution(sample_function)
        results.append(r)
    
    summary = get_results_summary(results)
    logger.info(f"Summary: {json.dumps(summary, indent=2)}")

if __name__ == "__main__":
    main()
