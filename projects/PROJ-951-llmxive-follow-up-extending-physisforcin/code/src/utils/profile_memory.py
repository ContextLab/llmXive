"""
Memory profiling script for measuring peak RAM usage.
Provides utilities to profile memory consumption of functions and the main process.
"""
import os
import sys
import time
import json
import logging
import threading
from dataclasses import dataclass, asdict, field
from typing import Optional, Callable, Any, Dict
from pathlib import Path

# Try to import psutil for accurate memory profiling
# If not available, we fall back to a basic implementation using resource module (Unix only)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    try:
        import resource
        HAS_RESOURCE = True
    except ImportError:
        HAS_RESOURCE = False
        logging.warning("Neither psutil nor resource module available for memory profiling.")


@dataclass
class MemoryProfileResult:
    """Data class to store memory profiling results."""
    function_name: str
    start_memory_mb: float
    peak_memory_mb: float
    end_memory_mb: float
    duration_seconds: float
    timestamp: str
    pid: int
    memory_limit_mb: Optional[float] = None
    exceeded_limit: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

class MemoryProfiler:
    """
    Context manager and utility class for profiling memory usage.
    Uses psutil if available, otherwise falls back to resource module (Unix).
    """
    
    def __init__(self, limit_mb: Optional[float] = None, logger: Optional[logging.Logger] = None):
        self.limit_mb = limit_mb
        self.logger = logger or logging.getLogger(__name__)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._peak_memory_mb = 0.0
        self._start_memory_mb = 0.0
        self._samples: list = []

    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        elif HAS_RESOURCE:
            # resource module only works on Unix and measures the max RSS of the process
            # We can only get the current limit or max usage, not instantaneous
            return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        else:
            self.logger.warning("No memory profiling backend available. Returning 0.0.")
            return 0.0

    def _monitor_memory(self):
        """Background thread to monitor memory usage at intervals."""
        while not self._stop_event.is_set():
            current = self._get_memory_mb()
            self._samples.append(current)
            if current > self._peak_memory_mb:
                self._peak_memory_mb = current
            time.sleep(0.05)  # Sample every 50ms

    def start(self):
        """Start memory monitoring."""
        self._start_memory_mb = self._get_memory_mb()
        self._peak_memory_mb = self._start_memory_mb
        self._samples = [self._start_memory_mb]
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self._thread.start()

    def stop(self) -> float:
        """Stop memory monitoring and return peak memory."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        # Final sample to ensure we capture end state
        final_memory = self._get_memory_mb()
        self._samples.append(final_memory)
        if final_memory > self._peak_memory_mb:
            self._peak_memory_mb = final_memory
        return self._peak_memory_mb

    def profile(self, func: Callable, *args, **kwargs) -> MemoryProfileResult:
        """Profile a function's memory usage."""
        start_time = time.time()
        self.start()
        
        try:
            result = func(*args, **kwargs)
        finally:
            end_time = time.time()
            peak = self.stop()
            duration = end_time - start_time
            end_memory = self._get_memory_mb()

        exceeded = False
        if self.limit_mb is not None and peak > self.limit_mb:
            exceeded = True
            self.logger.error(f"Memory limit exceeded: {peak:.2f} MB > {self.limit_mb} MB")

        return MemoryProfileResult(
            function_name=func.__name__,
            start_memory_mb=self._start_memory_mb,
            peak_memory_mb=peak,
            end_memory_mb=end_memory,
            duration_seconds=duration,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            pid=os.getpid(),
            memory_limit_mb=self.limit_mb,
            exceeded_limit=exceeded,
            details={
                "samples_count": len(self._samples),
                "avg_memory_mb": sum(self._samples) / len(self._samples) if self._samples else 0
            }
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

def get_current_memory_mb() -> float:
    """Get the current memory usage of the process in MB."""
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    elif HAS_RESOURCE:
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    else:
        return 0.0

def check_memory_limit(limit_mb: float) -> bool:
    """
    Check if current memory usage is within the specified limit.
    Returns True if within limit, False otherwise.
    """
    current = get_current_memory_mb()
    if current > limit_mb:
        logging.error(f"Memory usage {current:.2f} MB exceeds limit {limit_mb} MB")
        return False
    return True

def profile_memory(func: Callable, limit_mb: Optional[float] = None, 
                   output_path: Optional[str] = None) -> MemoryProfileResult:
    """
    Decorator to profile memory usage of a function.
    
    Args:
        func: The function to profile
        limit_mb: Optional memory limit in MB
        output_path: Optional path to save results as JSON
        
    Returns:
        MemoryProfileResult containing profiling data
    """
    profiler = MemoryProfiler(limit_mb=limit_mb)
    result = profiler.profile(func)
    
    if output_path:
        save_profile_result(result, output_path)
        
    return result

def profile_function(func: Callable, *args, limit_mb: Optional[float] = None, 
                     output_path: Optional[str] = None, **kwargs) -> MemoryProfileResult:
    """
    Profile a function call with given arguments.
    
    Args:
        func: Function to profile
        *args: Positional arguments for the function
        limit_mb: Optional memory limit in MB
        output_path: Optional path to save results as JSON
        **kwargs: Keyword arguments for the function
        
    Returns:
        MemoryProfileResult containing profiling data
    """
    profiler = MemoryProfiler(limit_mb=limit_mb)
    result = profiler.profile(func, *args, **kwargs)
    
    if output_path:
        save_profile_result(result, output_path)
        
    return result

def save_profile_result(result: MemoryProfileResult, path: str) -> None:
    """Save memory profiling result to a JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(asdict(result), f, indent=2)
    
    logging.info(f"Memory profile result saved to {path}")

def main():
    """Main function to demonstrate memory profiling."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Example function to profile
    def heavy_memory_function():
        """Simulate a memory-intensive operation."""
        logging.info("Starting memory-intensive operation...")
        data = []
        for i in range(1000000):
            data.append([i] * 100)
        time.sleep(1)
        logging.info(f"Created list with {len(data)} elements")
        return data

    # Profile the function
    logging.info("Profiling memory usage...")
    result = profile_function(
        heavy_memory_function,
        limit_mb=5000,  # 5 GB limit
        output_path="data/validation/memory_profile_result.json"
    )
    
    # Print results
    print(f"\nMemory Profile Results for '{result.function_name}':")
    print(f"  Start Memory: {result.start_memory_mb:.2f} MB")
    print(f"  Peak Memory:  {result.peak_memory_mb:.2f} MB")
    print(f"  End Memory:   {result.end_memory_mb:.2f} MB")
    print(f"  Duration:     {result.duration_seconds:.2f} seconds")
    print(f"  Timestamp:    {result.timestamp}")
    print(f"  PID:          {result.pid}")
    print(f"  Limit:        {result.memory_limit_mb} MB")
    print(f"  Exceeded:     {result.exceeded_limit}")
    
    if result.exceeded_limit:
        logging.error("Memory limit exceeded!")
        sys.exit(1)
    else:
        logging.info("Memory usage within limits.")

if __name__ == "__main__":
    main()
