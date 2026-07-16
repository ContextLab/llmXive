"""
Resource profiling module for monitoring memory and CPU usage.

Implements FR-006: Memory monitoring (hard limit) and wall-clock tracking.
"""
import os
import sys
import time
import resource
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional, Callable, TypeVar, Union
from dataclasses import dataclass, asdict
from contextlib import contextmanager

# Unit conversion constants
MB = 1024 * 1024
KB = 1024

class ProfilerError(Exception):
    """Base exception for profiler errors."""
    pass

class MemoryLimitExceededError(ProfilerError):
    """Raised when memory usage exceeds the configured hard limit."""
    pass

@dataclass
class ResourceMetrics:
    """Container for resource usage metrics."""
    wall_clock_seconds: float
    cpu_user_seconds: float
    cpu_system_seconds: float
    peak_memory_mb: float
    memory_limit_mb: Optional[float] = None
    exceeded_limit: bool = False
    timestamp: float = 0.0
    block_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        return asdict(self)

class Profiler:
    """
    Context manager and utility class for profiling code blocks and functions.
    
    Tracks wall-clock time, CPU usage, and memory consumption with optional
    hard memory limits.
    """
    
    def __init__(self, memory_limit_mb: Optional[float] = None, 
                 output_path: Optional[Union[str, Path]] = None):
        """
        Initialize the profiler.
        
        Args:
            memory_limit_mb: Hard memory limit in MB. If exceeded, raises MemoryLimitExceededError.
            output_path: Optional path to write metrics JSON after profiling.
        """
        self.memory_limit_mb = memory_limit_mb
        self.output_path = Path(output_path) if output_path else None
        self._start_time: float = 0.0
        self._start_cpu_user: float = 0.0
        self._start_cpu_sys: float = 0.0
        self._peak_memory: float = 0.0
        self._active: bool = False
        self._lock = threading.Lock()

    def _get_peak_memory_mb(self) -> float:
        """
        Get the peak memory usage of the current process in MB.
        
        Uses resource.getrusage for cross-platform compatibility.
        """
        # getrusage returns memory in KB on most Unix systems, bytes on macOS
        usage = resource.getrusage(resource.RUSAGE_SELF)
        mem_kb = usage.ru_maxrss
        
        # Handle platform differences: macOS reports in bytes, Linux in KB
        if sys.platform == 'darwin':
            return mem_kb / MB
        else:
            return mem_kb / KB

    def start(self) -> None:
        """Start profiling."""
        with self._lock:
            if self._active:
                raise ProfilerError("Profiler is already active")
            
            self._start_time = time.perf_counter()
            usage = resource.getrusage(resource.RUSAGE_SELF)
            self._start_cpu_user = usage.ru_utime
            self._start_cpu_sys = usage.ru_stime
            self._peak_memory = self._get_peak_memory_mb()
            self._active = True

    def stop(self, block_name: Optional[str] = None) -> ResourceMetrics:
        """
        Stop profiling and return metrics.
        
        Args:
            block_name: Optional name for the profiled block.
        
        Returns:
            ResourceMetrics containing the measured values.
        
        Raises:
            ProfilerError: If profiler was not started.
        """
        with self._lock:
            if not self._active:
                raise ProfilerError("Profiler was not started")
            
            end_time = time.perf_counter()
            usage = resource.getrusage(resource.RUSAGE_SELF)
            
            wall_clock = end_time - self._start_time
            cpu_user = usage.ru_utime - self._start_cpu_user
            cpu_sys = usage.ru_stime - self._start_cpu_sys
            current_peak = self._get_peak_memory_mb()
            peak_memory = max(self._peak_memory, current_peak)
            
            exceeded = False
            if self.memory_limit_mb is not None and peak_memory > self.memory_limit_mb:
                exceeded = True
                raise MemoryLimitExceededError(
                    f"Memory limit exceeded: {peak_memory:.2f} MB > {self.memory_limit_mb} MB"
                )
            
            metrics = ResourceMetrics(
                wall_clock_seconds=round(wall_clock, 4),
                cpu_user_seconds=round(cpu_user, 4),
                cpu_system_seconds=round(cpu_sys, 4),
                peak_memory_mb=round(peak_memory, 2),
                memory_limit_mb=self.memory_limit_mb,
                exceeded_limit=exceeded,
                timestamp=time.time(),
                block_name=block_name
            )
            
            self._active = False
            
            if self.output_path:
                self._save_metrics(metrics)
            
            return metrics

    def _save_metrics(self, metrics: ResourceMetrics) -> None:
        """Save metrics to the configured output path."""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)

    def __enter__(self) -> 'Profiler':
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.stop()
        # If an exception occurred (other than MemoryLimitExceededError),
        # we still want to stop cleanly if possible, but don't overwrite the exception
        elif exc_type is not MemoryLimitExceededError:
            try:
                self.stop()
            except ProfilerError:
                pass

@contextmanager
def profile_block(name: str, memory_limit_mb: Optional[float] = None):
    """
    Context manager to profile a specific code block.
    
    Args:
        name: Identifier for the block being profiled.
        memory_limit_mb: Optional hard memory limit for this block.
    
    Yields:
        None
    
    Raises:
        MemoryLimitExceededError: If memory limit is exceeded.
    
    Usage:
        with profile_block("data_processing", memory_limit_mb=4096):
            heavy_computation()
    """
    profiler = Profiler(memory_limit_mb=memory_limit_mb)
    profiler.start()
    try:
        yield
    finally:
        profiler.stop(block_name=name)

def profile_function(memory_limit_mb: Optional[float] = None):
    """
    Decorator to profile a function's resource usage.
    
    Args:
        memory_limit_mb: Optional hard memory limit for the function execution.
    
    Returns:
        Decorated function that returns the function's result and prints metrics.
    
    Usage:
        @profile_function(memory_limit_mb=2048)
        def my_function():
            return result
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            profiler = Profiler(memory_limit_mb=memory_limit_mb)
            profiler.start()
            try:
                result = func(*args, **kwargs)
                metrics = profiler.stop(block_name=func.__name__)
                print(f"Profiled '{func.__name__}': "
                      f"Wall={metrics.wall_clock_seconds:.3f}s, "
                      f"CPU={metrics.cpu_user_seconds + metrics.cpu_system_seconds:.3f}s, "
                      f"PeakMem={metrics.peak_memory_mb:.2f}MB")
                return result
            except MemoryLimitExceededError:
                raise
        return wrapper
    return decorator

def check_memory_limit(limit_mb: float) -> None:
    """
    Check if current memory usage exceeds a limit.
    
    Args:
        limit_mb: Memory limit in MB.
    
    Raises:
        MemoryLimitExceededError: If limit is exceeded.
    """
    current = get_peak_memory_mb()
    if current > limit_mb:
        raise MemoryLimitExceededError(
            f"Memory limit exceeded: {current:.2f} MB > {limit_mb} MB"
        )

def get_peak_memory_mb() -> float:
    """
    Get the current peak memory usage of the process in MB.
    
    Returns:
        Peak memory usage in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    mem_kb = usage.ru_maxrss
    
    if sys.platform == 'darwin':
        return mem_kb / MB
    else:
        return mem_kb / KB

def profile(func: Callable) -> Callable:
    """
    Simple decorator to profile a function and return metrics.
    
    Returns a tuple of (result, metrics_dict).
    
    Usage:
        @profile
        def my_func():
            return 42
        
        result, metrics = my_func()
    """
    def wrapper(*args, **kwargs):
        profiler = Profiler()
        profiler.start()
        try:
            result = func(*args, **kwargs)
            metrics = profiler.stop(block_name=func.__name__)
            return result, metrics.to_dict()
        except Exception as e:
            profiler.stop(block_name=func.__name__)
            raise
    return wrapper