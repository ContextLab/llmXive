"""
Profiling utilities for CPU/RAM and wall-clock time instrumentation.

Uses tracemalloc for memory profiling and time for wall-clock.
"""

import os
import time
import tracemalloc
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProfileResult:
    """Result container for profiling data."""
    start_time: float
    end_time: float
    wall_clock_ms: float
    peak_memory_mb: float
    current_memory_mb: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "wall_clock_ms": self.wall_clock_ms,
            "peak_memory_mb": self.peak_memory_mb,
            "current_memory_mb": self.current_memory_mb
        }

# Global profiling state
_profiling_active = False
_start_time = 0.0
_peak_memory = 0.0
_current_memory = 0.0

def get_process_memory_mb() -> float:
    """Get current process memory usage in MB."""
    if not _profiling_active:
        return 0.0
    
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)

def get_peak_memory_mb() -> float:
    """Get peak process memory usage in MB."""
    if not _profiling_active:
        return 0.0
    
    current, peak = tracemalloc.get_traced_memory()
    return peak / (1024 * 1024)

def start_profiling():
    """Start global profiling."""
    global _profiling_active, _start_time, _peak_memory, _current_memory
    
    if _profiling_active:
        logger.warning("Profiling already active.")
        return
        
    tracemalloc.start()
    _profiling_active = True
    _start_time = time.time()
    _peak_memory = 0.0
    _current_memory = 0.0
    logger.info("Profiling started.")

def stop_profiling() -> ProfileResult:
    """Stop global profiling and return results."""
    global _profiling_active, _start_time, _peak_memory, _current_memory
    
    if not _profiling_active:
        raise RuntimeError("Profiling not active.")
        
    end_time = time.time()
    current, peak = tracemalloc.get_traced_memory()
    
    current_mb = current / (1024 * 1024)
    peak_mb = peak / (1024 * 1024)
    wall_clock_ms = (end_time - _start_time) * 1000
    
    tracemalloc.stop()
    _profiling_active = False
    
    result = ProfileResult(
        start_time=_start_time,
        end_time=end_time,
        wall_clock_ms=wall_clock_ms,
        peak_memory_mb=peak_mb,
        current_memory_mb=current_mb
    )
    
    logger.info(f"Profiling stopped. Peak: {peak_mb:.2f} MB, Wall-clock: {wall_clock_ms:.2f} ms")
    return result

def reset_profiling():
    """Reset profiling state without stopping."""
    global _start_time, _peak_memory, _current_memory
    
    if not _profiling_active:
        return
        
    _start_time = time.time()
    _peak_memory = 0.0
    _current_memory = 0.0
    logger.info("Profiling reset.")

@contextmanager
def profile_block(label: str = "block") -> ContextManager[ProfileResult]:
    """Context manager to profile a code block."""
    if not _profiling_active:
        raise RuntimeError("Profiling not active. Call start_profiling() first.")
        
    start = time.time()
    tracemalloc.start()
    
    try:
        yield
    finally:
        end = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        wall_clock_ms = (end - start) * 1000
        peak_mb = peak / (1024 * 1024)
        current_mb = current / (1024 * 1024)
        
        result = ProfileResult(
            start_time=start,
            end_time=end,
            wall_clock_ms=wall_clock_ms,
            peak_memory_mb=peak_mb,
            current_memory_mb=current_mb
        )
        
        logger.info(f"[{label}] Wall-clock: {wall_clock_ms:.2f} ms, Peak: {peak_mb:.2f} MB")

def profile_function(func: Callable) -> Callable:
    """Decorator to profile a function."""
    def wrapper(*args, **kwargs):
        if not _profiling_active:
            return func(*args, **kwargs)
            
        start = time.time()
        tracemalloc.start()
        
        try:
            result = func(*args, **kwargs)
        finally:
            end = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            wall_clock_ms = (end - start) * 1000
            peak_mb = peak / (1024 * 1024)
            
            logger.info(f"[{func.__name__}] Wall-clock: {wall_clock_ms:.2f} ms, Peak: {peak_mb:.2f} MB")
            
        return result
        
    return wrapper

def measure_execution(func: Callable, *args, **kwargs) -> ProfileResult:
    """Measure execution of a single function call."""
    start = time.time()
    tracemalloc.start()
    
    try:
        result = func(*args, **kwargs)
    finally:
        end = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        wall_clock_ms = (end - start) * 1000
        peak_mb = peak / (1024 * 1024)
        current_mb = current / (1024 * 1024)
        
        return ProfileResult(
            start_time=start,
            end_time=end,
            wall_clock_ms=wall_clock_ms,
            peak_memory_mb=peak_mb,
            current_memory_mb=current_mb
        )

def main():
    """Test the profiling module."""
    start_profiling()
    
    # Simulate some work
    time.sleep(0.1)
    data = [i ** 2 for i in range(10000)]
    
    result = stop_profiling()
    print(f"Result: {result.to_dict()}")

if __name__ == "__main__":
    main()
