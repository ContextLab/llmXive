"""
Profiling utilities for CPU/RAM and wall-clock time instrumentation.

This module provides context managers and decorators to measure:
- Wall-clock execution time
- Peak and current memory usage (via tracemalloc)
- CPU time (via time.process_time)

All measurements are CPU-only compliant and do not require GPU resources.
"""

import os
import time
import tracemalloc
import logging
import json
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager, List, NamedTuple
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Type variable for decorators
T = TypeVar('T')

@dataclass
class ProfileResult:
    """Container for profiling results of a single operation."""
    operation_name: str
    wall_time_ms: float
    cpu_time_ms: float
    peak_memory_mb: float
    current_memory_mb: float
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

# Global state for tracking
_profiling_active: bool = False
_start_time: Optional[float] = None
_start_cpu_time: Optional[float] = None
_start_memory: Optional[float] = None
_peak_memory: float = 0.0
_results: List[ProfileResult] = []

def get_process_memory_mb() -> float:
    """
    Get current process memory usage in MB using tracemalloc.
    
    Returns:
        float: Memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        # If tracemalloc isn't active, try to get from psutil if available,
        # otherwise return 0.0 (tracemalloc should be started by start_profiling)
        return 0.0
    
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """
    Get peak memory usage since tracing started in MB.
    
    Returns:
        float: Peak memory usage in megabytes.
    """
    if not tracemalloc.is_tracing():
        return 0.0
    
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def start_profiling():
    """
    Start memory and time profiling.
    
    Initializes tracemalloc and records start times.
    """
    global _profiling_active, _start_time, _start_cpu_time, _start_memory, _peak_memory
    
    if _profiling_active:
        logger.warning("Profiling is already active. Skipping start.")
        return
    
    tracemalloc.start()
    _start_time = time.perf_counter()
    _start_cpu_time = time.process_time()
    _start_memory, _peak_memory = tracemalloc.get_traced_memory()
    _peak_memory = 0.0
    _results.clear()
    _profiling_active = True
    
    logger.info("Profiling started.")

def stop_profiling() -> Optional[ProfileResult]:
    """
    Stop profiling and return the aggregated result.
    
    Returns:
        ProfileResult: Aggregated profiling data, or None if not active.
    """
    global _profiling_active, _start_time, _start_cpu_time, _peak_memory
    
    if not _profiling_active:
        logger.warning("Profiling is not active. Cannot stop.")
        return None
    
    end_time = time.perf_counter()
    end_cpu_time = time.process_time()
    current_memory, peak_memory = tracemalloc.get_traced_memory()
    
    wall_time_ms = (end_time - _start_time) * 1000
    cpu_time_ms = (end_cpu_time - _start_cpu_time) * 1000
    peak_memory_mb = peak_memory / (1024 * 1024)
    current_memory_mb = current_memory / (1024 * 1024)
    
    result = ProfileResult(
        operation_name="global_session",
        wall_time_ms=wall_time_ms,
        cpu_time_ms=cpu_time_ms,
        peak_memory_mb=peak_memory_mb,
        current_memory_mb=current_memory_mb,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    )
    
    _results.append(result)
    _profiling_active = False
    tracemalloc.stop()
    
    logger.info(f"Profiling stopped. Peak RAM: {peak_memory_mb:.2f} MB, Wall Time: {wall_time_ms:.2f} ms.")
    return result

def reset_profiling():
    """Reset all profiling state without stopping tracemalloc if active."""
    global _start_time, _start_cpu_time, _peak_memory, _results
    
    _start_time = None
    _start_cpu_time = None
    _peak_memory = 0.0
    _results.clear()
    
    if tracemalloc.is_tracing():
        tracemalloc.reset_peak()
        logger.info("Profiling state reset.")

@contextmanager
def profile_block(label: str = "unnamed_block") -> ContextManager[Optional[ProfileResult]]:
    """
    Context manager to profile a specific code block.
    
    Args:
        label: Identifier for the block being profiled.
        
    Yields:
        ProfileResult: The result of the profiling for this block.
        
    Example:
        with profile_block("data_loading") as result:
            load_data()
        print(f"Block took {result.wall_time_ms} ms")
    """
    if not _profiling_active:
        logger.warning("Profiling not active. Wrapping block without timing.")
        yield None
        return
    
    start_time = time.perf_counter()
    start_cpu = time.process_time()
    start_mem, _ = tracemalloc.get_traced_memory()
    
    try:
        yield
    finally:
        end_time = time.perf_counter()
        end_cpu = time.process_time()
        end_mem, peak_mem = tracemalloc.get_traced_memory()
        
        # Update global peak if this block exceeded it
        global _peak_memory
        if peak_mem > _peak_memory:
            _peak_memory = peak_mem
        
        wall_time_ms = (end_time - start_time) * 1000
        cpu_time_ms = (end_cpu - start_cpu) * 1000
        peak_memory_mb = peak_mem / (1024 * 1024)
        current_memory_mb = end_mem / (1024 * 1024)
        
        result = ProfileResult(
            operation_name=label,
            wall_time_ms=wall_time_ms,
            cpu_time_ms=cpu_time_ms,
            peak_memory_mb=peak_memory_mb,
            current_memory_mb=current_memory_mb,
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        
        _results.append(result)
        logger.debug(f"Profiled block '{label}': {wall_time_ms:.2f} ms, {peak_memory_mb:.2f} MB peak.")

@contextmanager
def profile_function(label: str = None) -> ContextManager[Optional[ProfileResult]]:
    """
    Context manager specifically designed to wrap function execution.
    Alias for profile_block but with semantic clarity for function wrapping.
    
    Args:
        label: Optional label. If None, the function name will be used.
    """
    yield from profile_block(label or "function_execution")

def profile_function_decorator(label: str = None) -> Callable[[Callable[[T], T]], Callable[[T], T]]:
    """
    Decorator to profile a function.
    
    Args:
        label: Optional label. If None, the function name is used.
        
    Returns:
        Decorated function that logs profiling data.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            block_label = label or func.__name__
            with profile_block(block_label) as result:
                return func(*args, **kwargs)
        return wrapper
    return decorator

def measure_execution(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Execute a function and return its profiling results.
    
    Args:
        func: The function to execute.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        Dict containing execution results and profiling metrics.
    """
    if not _profiling_active:
        start_profiling()
    
    block_label = func.__name__
    with profile_block(block_label) as result:
        output = func(*args, **kwargs)
    
    return {
        "output": output,
        "profile": result.to_dict() if result else {}
    }

def get_results_summary() -> List[Dict[str, Any]]:
    """
    Get a summary of all recorded profiling results.
    
    Returns:
        List of dictionaries containing profile data.
    """
    return [r.to_dict() for r in _results]

def save_results_to_file(filepath: str, results: Optional[List[ProfileResult]] = None):
    """
    Save profiling results to a JSON file.
    
    Args:
        filepath: Path to the output file.
        results: Optional list of results. If None, uses global _results.
    """
    data = results if results is not None else _results
    if not data:
        logger.warning("No results to save.")
        return
    
    # Ensure directory exists
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump([r.to_dict() for r in data], f, indent=2)
    
    logger.info(f"Profiling results saved to {filepath}")

def main():
    """
    Main entry point for testing the profiling module standalone.
    Runs a dummy task to demonstrate profiling capabilities.
    """
    logger.info("Running profiling module self-test...")
    
    start_profiling()
    
    # Simulate a task
    with profile_block("dummy_task_simulation"):
        time.sleep(0.1)  # Simulate work
        data = [i * i for i in range(10000)]  # Simulate memory usage
        _ = sum(data)
    
    result = stop_profiling()
    
    if result:
        print(f"Self-test completed.")
        print(f"Operation: {result.operation_name}")
        print(f"Wall Time: {result.wall_time_ms:.2f} ms")
        print(f"Peak RAM: {result.peak_memory_mb:.2f} MB")
        
        # Save results
        save_results_to_file("data/processed/profiling_self_test.json")
    else:
        logger.error("Self-test failed: No result returned.")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())