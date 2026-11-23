"""
Memory profiling utilities for the llmXive pipeline.
Measures peak RAM usage for verification tasks.
"""
import os
import sys
import time
import json
import logging
import threading
from dataclasses import dataclass, asdict
from typing import Optional, Callable, Any, Dict
from pathlib import Path

# Try to import psutil for accurate memory monitoring
# If not available, fall back to /proc on Linux or basic os methods
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available. Using fallback memory estimation.")


@dataclass
class MemoryProfileResult:
    """Result container for memory profiling."""
    peak_memory_mb: float
    start_memory_mb: float
    end_memory_mb: float
    duration_seconds: float
    timestamp: str
    task_name: Optional[str] = None
    pid: Optional[int] = None
    platform: str = sys.platform

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __str__(self) -> str:
        return (
            f"MemoryProfileResult(peak={self.peak_memory_mb:.2f}MB, "
            f"start={self.start_memory_mb:.2f}MB, "
            f"duration={self.duration_seconds:.2f}s)"
        )


class MemoryProfiler:
    """
    Context manager and utility class for profiling memory usage.
    Tracks peak memory usage during a block of code execution.
    """
    def __init__(self, task_name: Optional[str] = None):
        self.task_name = task_name
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.start_memory: float = 0.0
        self.peak_memory: float = 0.0
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring: threading.Event = threading.Event()
        self._current_process = psutil.Process() if PSUTIL_AVAILABLE else None

    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        if PSUTIL_AVAILABLE and self._current_process:
            # RSS (Resident Set Size) is the portion of memory occupied by a process
            return self._current_process.memory_info().rss / (1024 * 1024)
        else:
            # Fallback for Linux
            if sys.platform == 'linux':
                try:
                    with open('/proc/self/status', 'r') as f:
                        for line in f:
                            if line.startswith('VmRSS:'):
                                # VmRSS is in kB
                                return float(line.split()[1]) / 1024.0
                except Exception:
                    pass
            # Ultimate fallback: 0.0 (will cause errors if used for logic, but allows import)
            return 0.0

    def _monitor_loop(self):
        """Background thread to record peak memory."""
        while not self.stop_monitoring.is_set():
            current = self._get_memory_mb()
            if current > self.peak_memory:
                self.peak_memory = current
            time.sleep(0.1)  # Sample every 100ms

    def start(self):
        """Start profiling."""
        self.start_time = time.time()
        self.start_memory = self._get_memory_mb()
        self.peak_memory = self.start_memory
        self.stop_monitoring.clear()
        
        if PSUTIL_AVAILABLE:
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

    def stop(self) -> MemoryProfileResult:
        """Stop profiling and return results."""
        self.end_time = time.time()
        self.stop_monitoring.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        
        # Final check
        final_memory = self._get_memory_mb()
        if final_memory > self.peak_memory:
            self.peak_memory = final_memory

        duration = self.end_time - self.start_time
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())

        return MemoryProfileResult(
            peak_memory_mb=self.peak_memory,
            start_memory_mb=self.start_memory,
            end_memory_mb=final_memory,
            duration_seconds=duration,
            timestamp=timestamp,
            task_name=self.task_name,
            pid=os.getpid()
        )

    def __enter__(self) -> 'MemoryProfiler':
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def get_current_memory_mb() -> float:
    """
    Utility function to get current memory usage of the process in MB.
    
    Returns:
        float: Current memory usage in MB.
    """
    if PSUTIL_AVAILABLE:
        return psutil.Process().memory_info().rss / (1024 * 1024)
    else:
        if sys.platform == 'linux':
            try:
                with open('/proc/self/status', 'r') as f:
                    for line in f:
                        if line.startswith('VmRSS:'):
                            return float(line.split()[1]) / 1024.0
            except Exception:
                pass
        return 0.0


def check_memory_limit(limit_mb: float, current_memory_mb: Optional[float] = None) -> bool:
    """
    Check if current memory usage is within a specified limit.
    
    Args:
        limit_mb: Maximum allowed memory in MB.
        current_memory_mb: Optional pre-calculated memory usage. If None, calculates it.
        
    Returns:
        bool: True if within limit, False otherwise.
        
    Raises:
        MemoryError: If memory usage exceeds the limit.
    """
    if current_memory_mb is None:
        current_memory_mb = get_current_memory_mb()
        
    if current_memory_mb > limit_mb:
        raise MemoryError(
            f"Memory limit exceeded: {current_memory_mb:.2f}MB > {limit_mb}MB"
        )
    return True


def profile_memory(func: Callable) -> Callable:
    """
    Decorator to profile memory usage of a function.
    
    Args:
        func: The function to profile.
        
    Returns:
        Wrapped function that profiles memory.
    """
    def wrapper(*args, **kwargs):
        profiler = MemoryProfiler(task_name=func.__name__)
        result = None
        try:
            with profiler:
                result = func(*args, **kwargs)
            profile_result = profiler.stop()
            logging.info(f"Memory profile for {func.__name__}: {profile_result}")
            return result, profile_result
        except Exception as e:
            # If we are inside the context manager, ensure we stop it
            try:
                profile_result = profiler.stop()
                logging.error(f"Function {func.__name__} failed with error: {e}. Memory profile: {profile_result}")
            except Exception:
                pass
            raise e
    return wrapper


def profile_function(
    func: Callable, 
    *args, 
    task_name: Optional[str] = None, 
    **kwargs
) -> Tuple[Any, MemoryProfileResult]:
    """
    Run a function and profile its memory usage.
    
    Args:
        func: Function to execute.
        *args: Positional arguments for the function.
        task_name: Name for the profile result.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        Tuple of (function_result, MemoryProfileResult)
    """
    profiler = MemoryProfiler(task_name=task_name or func.__name__)
    result = None
    with profiler:
        result = func(*args, **kwargs)
    profile_result = profiler.stop()
    return result, profile_result


def save_profile_result(
    result: MemoryProfileResult, 
    output_path: str, 
    append: bool = True
) -> Path:
    """
    Save a memory profile result to a JSON file.
    
    Args:
        result: The profile result to save.
        output_path: Path to the output JSON file.
        append: If True, append to existing file (as JSONL). If False, overwrite.
        
    Returns:
        Path to the saved file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    data = result.to_dict()
    json_str = json.dumps(data)
    
    if append and path.exists():
        with open(path, 'a') as f:
            f.write(json_str + '\n')
    else:
        with open(path, 'w') as f:
            f.write(json_str + '\n')
            
    return path


def main():
    """
    Main entry point for command-line memory profiling.
    Usage: python -m src.utils.profile_memory [task_name]
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    task_name = sys.argv[1] if len(sys.argv) > 1 else "CLI_Profiling_Test"
    
    logging.info(f"Starting memory profile for: {task_name}")
    
    # Simulate some work to demonstrate profiling
    profiler = MemoryProfiler(task_name=task_name)
    
    try:
        with profiler:
            # Simulate memory allocation
            data = []
            for i in range(100000):
                data.append({"id": i, "value": "x" * 100})
            time.sleep(1.0)  # Hold memory for a second
            logging.info(f"Allocated list with {len(data)} items")
            
        result = profiler.stop()
        logging.info(f"Profile complete: {result}")
        print(f"Peak Memory: {result.peak_memory_mb:.2f} MB")
        
        # Save result
        output_file = "data/validation/memory_profile.jsonl"
        save_profile_result(result, output_file)
        logging.info(f"Result saved to: {output_file}")
        
    except Exception as e:
        logging.error(f"Profiling failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
