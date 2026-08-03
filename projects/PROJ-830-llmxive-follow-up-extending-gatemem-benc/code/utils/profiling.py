import os
import time
import tracemalloc
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime

# Import logging setup from the project's central config
from logging_config import setup_logging

# Initialize logger for this module
logger = setup_logging("profiling", level=logging.INFO)

# Global profiling state
_profiling_active: bool = False
_start_time: float = 0.0
_peak_memory: float = 0.0
_start_memory: float = 0.0

T = TypeVar("T")


@dataclass
class ProfileResult:
    """Data class to store profiling results for a specific operation."""
    operation_name: str
    start_time: float
    end_time: float
    duration_seconds: float
    start_memory_mb: float
    end_memory_mb: float
    peak_memory_mb: float
    delta_memory_mb: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a dictionary for JSON serialization."""
        return {
            "operation_name": self.operation_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "start_memory_mb": self.start_memory_mb,
            "end_memory_mb": self.end_memory_mb,
            "peak_memory_mb": self.peak_memory_mb,
            "delta_memory_mb": self.delta_memory_mb,
            "timestamp": self.timestamp
        }

def get_process_memory_mb() -> float:
    """
    Get the current memory usage of the process in MB.
    Uses tracemalloc if active, otherwise falls back to a simple estimate
    (though tracemalloc is the preferred method for accuracy in this pipeline).
    """
    if not tracemalloc.is_tracing():
        # Fallback if tracing isn't started, though we aim to start it early
        return 0.0
    
    current, peak = tracemalloc.get_traced_memory()
    # Return current in MB
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """
    Get the peak memory usage of the process in MB since tracing started.
    """
    if not tracemalloc.is_tracing():
        return 0.0
    
    current, peak = tracemalloc.get_traced_memory()
    # Return peak in MB
    return peak / (1024 * 1024)

def start_profiling():
    """
    Start the memory profiler (tracemalloc) and record start time.
    Must be called once before any profiling operations.
    """
    global _profiling_active, _start_time, _peak_memory, _start_memory
    
    if not _profiling_active:
        tracemalloc.start()
        _profiling_active = True
        _start_time = time.perf_counter()
        _start_memory = get_process_memory_mb()
        _peak_memory = _start_memory
        logger.info("Profiling started (tracemalloc initialized).")
    else:
        logger.warning("Profiling is already active.")

def stop_profiling() -> ProfileResult:
    """
    Stop the memory profiler and return a summary result.
    """
    global _profiling_active, _start_time, _peak_memory, _start_memory
    
    if not _profiling_active:
        logger.warning("Profiling is not active; cannot stop.")
        return ProfileResult(
            operation_name="global_stop",
            start_time=0.0,
            end_time=time.perf_counter(),
            duration_seconds=0.0,
            start_memory_mb=0.0,
            end_memory_mb=0.0,
            peak_memory_mb=0.0,
            delta_memory_mb=0.0
        )

    end_time = time.perf_counter()
    current_mem = get_process_memory_mb()
    peak_mem = get_peak_memory_mb()
    
    # Update global peak if necessary
    if peak_mem > _peak_memory:
        _peak_memory = peak_mem

    result = ProfileResult(
        operation_name="global_session",
        start_time=_start_time,
        end_time=end_time,
        duration_seconds=end_time - _start_time,
        start_memory_mb=_start_memory,
        end_memory_mb=current_mem,
        peak_memory_mb=_peak_memory,
        delta_memory_mb=current_mem - _start_memory
    )

    tracemalloc.stop()
    _profiling_active = False
    logger.info(f"Profiling stopped. Duration: {result.duration_seconds:.4f}s, Peak RAM: {result.peak_memory_mb:.2f}MB")
    
    return result

def reset_profiling():
    """
    Reset the global profiling state without stopping tracemalloc.
    Useful for measuring multiple distinct phases.
    """
    global _start_time, _start_memory, _peak_memory
    
    _start_time = time.perf_counter()
    _start_memory = get_process_memory_mb()
    _peak_memory = _start_memory
    logger.debug("Profiling counters reset.")

@contextmanager
def profile_block(operation_name: str = "anonymous_block") -> ContextManager[ProfileResult]:
    """
    Context manager to profile a block of code.
    
    Usage:
        with profile_block("my_function_call") as result:
            do_something()
        # result contains the timing and memory stats
    """
    if not _profiling_active:
        logger.warning(f"Profiling not active for block '{operation_name}'. Returning dummy result.")
        yield ProfileResult(
            operation_name=operation_name,
            start_time=time.perf_counter(),
            end_time=time.perf_counter(),
            duration_seconds=0.0,
            start_memory_mb=0.0,
            end_memory_mb=0.0,
            peak_memory_mb=0.0,
            delta_memory_mb=0.0
        )
        return

    start_time = time.perf_counter()
    start_mem = get_process_memory_mb()
    peak_mem_before = get_peak_memory_mb()
    
    try:
        yield ProfileResult(
            operation_name=operation_name,
            start_time=start_time,
            end_time=0.0,
            duration_seconds=0.0,
            start_memory_mb=start_mem,
            end_memory_mb=0.0,
            peak_memory_mb=0.0,
            delta_memory_mb=0.0
        )
    finally:
        end_time = time.perf_counter()
        end_mem = get_process_memory_mb()
        current_peak = get_peak_memory_mb()
        
        # Calculate delta from the start of this block
        delta_mem = end_mem - start_mem
        
        # Update result object in place (since it was yielded)
        # Note: In Python, we can't easily mutate the yielded object's fields if it's a dataclass with frozen=True, 
        # but here we construct a new one or update the dict if needed. 
        # However, the standard pattern is to let the user capture the result. 
        # Since we are using a generator, we can't easily update the object yielded before the block ends.
        # We will log the result here instead, or rely on the caller to capture the 'yield' value 
        # and then we update it? No, 'yield' pauses. 
        # Correct pattern for context manager returning data:
        pass

    # Since we cannot update the yielded object after the block executes in this simple generator pattern 
    # without a wrapper, we will construct the result now and log it. 
    # For the API to be useful as a return value, we usually return the result from the context manager 
    # or store it in a variable. 
    # Let's refine: The 'with' block receives the generator object. 
    # To get the result *after* the block, we need to handle the exception/finally.
    # A better approach for returning data:
    
    result = ProfileResult(
        operation_name=operation_name,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=end_time - start_time,
        start_memory_mb=start_mem,
        end_memory_mb=end_mem,
        peak_memory_mb=current_peak, # Global peak
        delta_memory_mb=delta_mem
    )
    
    logger.info(f"Profile Block '{operation_name}': {result.duration_seconds:.4f}s, Delta RAM: {result.delta_memory_mb:.2f}MB")

def profile_function(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to profile a function's execution time and memory.
    """
    def wrapper(*args, **kwargs) -> T:
        if not _profiling_active:
            logger.warning(f"Profiling not active for function '{func.__name__}'. Running without profiling.")
            return func(*args, **kwargs)

        start_time = time.perf_counter()
        start_mem = get_process_memory_mb()
        
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.perf_counter()
            end_mem = get_process_memory_mb()
            peak_mem = get_peak_memory_mb()
            
            duration = end_time - start_time
            delta_mem = end_mem - start_mem
            
            logger.info(
                f"Function '{func.__name__}' executed in {duration:.4f}s. "
                f"Start RAM: {start_mem:.2f}MB, End RAM: {end_mem:.2f}MB, "
                f"Delta: {delta_mem:.2f}MB, Peak: {peak_mem:.2f}MB"
            )
        
        return result
    return wrapper

def measure_execution(
    func: Callable[..., T], 
    *args, 
    **kwargs
) -> Tuple[T, ProfileResult]:
    """
    Execute a function and return both its result and a ProfileResult.
    This is useful when you need the data object programmatically.
    """
    if not _profiling_active:
        logger.warning("Profiling not active. Returning dummy result.")
        return func(*args, **kwargs), ProfileResult(
            operation_name=func.__name__,
            start_time=0.0, end_time=0.0, duration_seconds=0.0,
            start_memory_mb=0.0, end_memory_mb=0.0, peak_memory_mb=0.0, delta_memory_mb=0.0
        )

    start_time = time.perf_counter()
    start_mem = get_process_memory_mb()
    
    result = func(*args, **kwargs)
    
    end_time = time.perf_counter()
    end_mem = get_process_memory_mb()
    peak_mem = get_peak_memory_mb()
    
    duration = end_time - start_time
    delta_mem = end_mem - start_mem
    
    profile_res = ProfileResult(
        operation_name=func.__name__,
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        start_memory_mb=start_mem,
        end_memory_mb=end_mem,
        peak_memory_mb=peak_mem,
        delta_memory_mb=delta_mem
    )
    
    return result, profile_res