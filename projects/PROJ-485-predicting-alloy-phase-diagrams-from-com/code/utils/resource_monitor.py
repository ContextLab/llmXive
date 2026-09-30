import os
import sys
import time
import json
import psutil
from typing import Optional, Dict, Any, Callable, TypeVar
from functools import wraps
import threading

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

MAX_EXECUTION_TIME_SECONDS = 14400
MAX_MEMORY_GB = 7.0
MONITOR_INTERVAL_SECONDS = 30

T = TypeVar('T')

def get_peak_memory_gb() -> float:
    """
    Get the current peak memory usage of the process in GB.
    Uses psutil to get the maximum resident set size.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    # rss is in bytes, convert to GB
    return mem_info.rss / (1024 ** 3)

def check_resource_constraints(execution_time: int, peak_memory_gb: float) -> bool:
    """
    Checks if execution time or memory usage exceeds limits.
    Returns True if limits are exceeded (HALT condition), False otherwise.
    """
    if execution_time > MAX_EXECUTION_TIME_SECONDS:
        log_error(
            ErrorCode.RESOURCE_LIMIT_EXCEEDED,
            f"Execution time {execution_time}s exceeds limit {MAX_EXECUTION_TIME_SECONDS}s"
        )
        return True
    if peak_memory_gb > MAX_MEMORY_GB:
        log_error(
            ErrorCode.RESOURCE_LIMIT_EXCEEDED,
            f"Peak memory {peak_memory_gb:.2f}GB exceeds limit {MAX_MEMORY_GB}GB"
        )
        return True
    return False

def log_resource_usage(resource_log_path: str, execution_time: int, peak_memory_gb: float):
    """
    Logs execution time and peak memory to the specified JSON file.
    """
    log_data = {
        "execution_time_seconds": execution_time,
        "peak_memory_gb": round(peak_memory_gb, 4)
    }
    try:
        os.makedirs(os.path.dirname(resource_log_path), exist_ok=True)
        with open(resource_log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        log_info("RESOURCE_MONITOR", f"Resource usage logged to {resource_log_path}: {log_data}")
    except Exception as e:
        log_error("RESOURCE_MONITOR", f"Failed to write resource log: {e}")

def resource_monitor_wrapper(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to monitor execution time and peak memory usage of a function.
    Checks resource constraints after execution and logs results.
    If constraints are violated, it raises a RuntimeError with the specific error code.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        resource_log_path = kwargs.pop('resource_log_path', 'data/artifacts/resource_log.json')
        
        start_time = time.time()
        peak_memory = 0.0
        stop_event = threading.Event()
        monitor_thread = None

        def monitor_loop():
            nonlocal peak_memory
            while not stop_event.is_set():
                current_mem = get_peak_memory_gb()
                if current_mem > peak_memory:
                    peak_memory = current_mem
                time.sleep(MONITOR_INTERVAL_SECONDS)

        try:
            # Start monitoring thread
            monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitor_thread.start()

            # Execute the wrapped function
            result = func(*args, **kwargs)

        finally:
            # Stop monitoring
            stop_event.set()
            if monitor_thread:
                monitor_thread.join(timeout=1)

        end_time = time.time()
        execution_time = int(end_time - start_time)

        # Ensure we have the final peak memory measurement
        final_mem = get_peak_memory_gb()
        if final_mem > peak_memory:
            peak_memory = final_mem

        # Log results
        log_resource_usage(resource_log_path, execution_time, peak_memory)

        # Check constraints
        if check_resource_constraints(execution_time, peak_memory):
            raise RuntimeError(f"{ErrorCode.RESOURCE_LIMIT_EXCEEDED}: Resource limits exceeded")

        return result
    return wrapper

def main():
    """
    Main entry point for testing the resource monitor directly.
    """
    logger.info("Starting resource monitor test...")
    
    # Example usage of the wrapper
    @resource_monitor_wrapper
    def simulated_task(resource_log_path: str = "data/artifacts/resource_log.json"):
        log_info("SIMULATED_TASK", "Running simulated heavy task...")
        time.sleep(2) # Simulate work
        # Simulate memory usage by allocating a list
        _ = [i for i in range(1000000)]
        time.sleep(1)
        log_info("SIMULATED_TASK", "Task completed.")
        return "success"

    try:
        result = simulated_task()
        log_info("RESOURCE_MONITOR", f"Task result: {result}")
    except RuntimeError as e:
        log_error("RESOURCE_MONITOR", str(e))
        sys.exit(1)
    except Exception as e:
        log_error("RESOURCE_MONITOR", f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
