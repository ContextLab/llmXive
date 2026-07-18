import os
import sys
import time
import json
import logging
import threading
import resource
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict
import psutil

from src.utils.logging import get_logger, setup_default_loggers

# Initialize logger for this module
logger = get_logger(__name__)

@dataclass
class MemoryProfileResult:
    """Data class to hold memory profiling results."""
    function_name: str
    start_time: float
    end_time: float
    duration_seconds: float
    peak_memory_mb: float
    current_memory_mb: float
    memory_increase_mb: float
    return_value: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for JSON serialization."""
        return asdict(self)

class MemoryProfiler:
    """
    Context manager and utility class for profiling memory usage.
    Uses psutil for cross-platform memory monitoring.
    """
    def __init__(self, func_name: str = "unknown", logger: Optional[logging.Logger] = None):
        self.func_name = func_name
        self.logger = logger or get_logger(__name__)
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.peak_memory_mb: float = 0.0
        self.current_memory_mb: float = 0.0
        self.memory_increase_mb: float = 0.0
        self._thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._monitor_interval = 0.1  # 100ms

    def _monitor_loop(self):
        """Background thread to monitor peak memory usage."""
        process = psutil.Process(os.getpid())
        max_mem = 0.0
        while not self._stop_monitoring.is_set():
            try:
                mem_info = process.memory_info()
                current_mb = mem_info.rss / (1024 * 1024)
                if current_mb > max_mem:
                    max_mem = current_mb
                time.sleep(self._monitor_interval)
            except Exception as e:
                self.logger.warning(f"Memory monitoring error: {e}")
                break
        self.peak_memory_mb = max_mem

    def __enter__(self):
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.current_memory_mb = process.memory_info().rss / (1024 * 1024)
        self._stop_monitoring.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stop_monitoring.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        self.end_time = time.time()
        process = psutil.Process(os.getpid())
        final_mem = process.memory_info().rss / (1024 * 1024)
        self.current_memory_mb = final_mem
        self.memory_increase_mb = final_mem - self.current_memory_mb
        
        if exc_type is None:
            self.logger.info(
                f"Memory profile for '{self.func_name}': "
                f"Duration={self.end_time - self.start_time:.3f}s, "
                f"Peak={self.peak_memory_mb:.2f}MB, "
                f"Final={self.current_memory_mb:.2f}MB"
            )
        return False

    def get_result(self, return_value: Optional[Any] = None, error: Optional[str] = None) -> MemoryProfileResult:
        """Create a MemoryProfileResult object from the current state."""
        return MemoryProfileResult(
            function_name=self.func_name,
            start_time=self.start_time,
            end_time=self.end_time,
            duration_seconds=self.end_time - self.start_time,
            peak_memory_mb=self.peak_memory_mb,
            current_memory_mb=self.current_memory_mb,
            memory_increase_mb=self.memory_increase_mb,
            return_value=return_value,
            error=error
        )

def get_current_memory_mb() -> float:
    """
    Get the current memory usage of the current process in MB.
    
    Returns:
        Current RSS memory usage in Megabytes.
    """
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def check_memory_limit(limit_mb: float) -> bool:
    """
    Check if current memory usage is within the specified limit.
    
    Args:
        limit_mb: Maximum allowed memory usage in MB.
        
    Returns:
        True if current usage is below limit, False otherwise.
    """
    current = get_current_memory_mb()
    if current > limit_mb:
        logger.warning(f"Memory limit exceeded: {current:.2f}MB > {limit_mb}MB")
        return False
    return True

def profile_memory(func: Callable) -> Callable:
    """
    Decorator to profile memory usage of a function.
    
    Args:
        func: The function to profile.
        
    Returns:
        Wrapped function that profiles memory usage.
    """
    def wrapper(*args, **kwargs):
        profiler = MemoryProfiler(func.__name__)
        try:
            with profiler:
                result = func(*args, **kwargs)
                profile_result = profiler.get_result(return_value=result)
                logger.info(f"Profiled {func.__name__}: Peak={profile_result.peak_memory_mb:.2f}MB")
                return result, profile_result
        except Exception as e:
            profile_result = profiler.get_result(error=str(e))
            logger.error(f"Profiled {func.__name__} failed: {e}")
            raise
    return wrapper

def profile_function(func: Callable, *args, **kwargs) -> MemoryProfileResult:
    """
    Profile a function call and return the memory profile result.
    
    Args:
        func: The function to profile.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        MemoryProfileResult containing timing and memory statistics.
    """
    profiler = MemoryProfiler(func.__name__)
    result = None
    error = None
    try:
        with profiler:
            result = func(*args, **kwargs)
            return profiler.get_result(return_value=result)
    except Exception as e:
        error = str(e)
        return profiler.get_result(error=error)

def save_profile_result(result: MemoryProfileResult, output_path: Union[str, Path]) -> None:
    """
    Save a memory profile result to a JSON file.
    
    Args:
        result: The MemoryProfileResult to save.
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = result.to_dict()
    # Remove non-serializable fields if any
    if 'return_value' in data and not isinstance(data['return_value'], (str, int, float, bool, type(None), list, dict)):
        data['return_value'] = str(data['return_value'])
        
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved memory profile to {output_path}")

def main():
    """
    Main entry point for memory profiling demonstration.
    Profiles a sample memory-intensive operation and saves results.
    """
    setup_default_loggers()
    
    output_dir = Path("data/eval")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "memory_profile_sample.json"
    
    logger.info("Starting memory profiling demonstration...")
    
    def memory_intensive_operation():
        """Simulate a memory-intensive operation."""
        # Allocate a list of integers to simulate memory usage
        data = []
        for i in range(1000000):
            data.append(i * 2)
        time.sleep(0.5)  # Simulate processing time
        return len(data)
    
    # Profile the function
    result = profile_function(memory_intensive_operation)
    
    if result.error:
        logger.error(f"Profiling failed: {result.error}")
        sys.exit(1)
    
    # Save the result
    save_profile_result(result, output_file)
    
    # Verify the file was created
    if output_file.exists():
        logger.info(f"Memory profile saved successfully to {output_file}")
        logger.info(f"Peak memory: {result.peak_memory_mb:.2f} MB")
        logger.info(f"Duration: {result.duration_seconds:.3f} seconds")
    else:
        logger.error("Failed to create output file")
        sys.exit(1)

if __name__ == "__main__":
    main()
