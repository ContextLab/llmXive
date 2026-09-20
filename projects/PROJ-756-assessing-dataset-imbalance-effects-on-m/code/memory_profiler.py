import os
import sys
import time
import csv
import logging
from pathlib import Path
from typing import Callable, Any, Optional

# Try to import resource for memory usage; fallback to psutil if available
try:
    import resource
    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_memory_usage_mb() -> float:
    """
    Returns the current memory usage of the process in MB.
    Uses resource (Unix) or psutil (cross-platform).
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    elif HAS_RESOURCE:
        # Get max RSS (peak memory) in bytes
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on some others. Usually KB on Linux.
        # To be safe, we assume KB on Linux which is standard for resource module.
        return usage.ru_maxrss / 1024.0
    else:
        logger.warning("Neither psutil nor resource module available for memory profiling.")
        return 0.0

class MemoryProfiler:
    """
    Context manager and decorator to profile memory usage of functions.
    Logs peak memory usage to a CSV file.
    """
    def __init__(self, output_path: str, function_name: str):
        self.output_path = output_path
        self.function_name = function_name
        self.start_time: Optional[float] = None
        self.start_memory: float = 0.0
        self.peak_memory: float = 0.0

    def __enter__(self):
        self.start_time = time.time()
        self.start_memory = get_memory_usage_mb()
        self.peak_memory = self.start_memory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_memory = get_memory_usage_mb()
        if end_memory > self.peak_memory:
            self.peak_memory = end_memory
        
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.start_time))
        self._log_result(timestamp)

    def _log_result(self, timestamp: str):
        """Append the result to the CSV file."""
        file_exists = os.path.exists(self.output_path)
        
        with open(self.output_path, mode='a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'peak_memory_mb', 'function_name'])
            writer.writerow([timestamp, f"{self.peak_memory:.2f}", self.function_name])
        
        logger.info(f"Memory profile logged for {self.function_name}: {self.peak_memory:.2f} MB")

def profile_memory(output_path: str = "results/memory_profile.csv"):
    """
    Decorator factory to profile memory usage of a function.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            profiler = MemoryProfiler(output_path, func.__name__)
            with profiler:
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

def profile_function(func: Callable, output_path: str = "results/memory_profile.csv", *args, **kwargs) -> Any:
    """
    Convenience function to run a function under memory profiling.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    profiler = MemoryProfiler(output_path, func.__name__)
    with profiler:
        result = func(*args, **kwargs)
    return result

def ensure_results_directory():
    """Helper to ensure results directory exists."""
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

if __name__ == "__main__":
    # Simple test if run directly
    ensure_results_directory()
    output_file = "results/memory_profile.csv"
    
    @profile_memory(output_file)
    def dummy_test():
        data = [i for i in range(1000000)]
        time.sleep(0.1)
        return sum(data)
    
    print("Running dummy test to verify profiling...")
    dummy_test()
    print(f"Profile written to {output_file}")
