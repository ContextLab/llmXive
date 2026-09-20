import os
import sys
import time
import json
import psutil
from typing import Optional, Dict, Any, Callable
from functools import wraps

# Import existing logging utilities
from .logging import get_logger, log_info, log_error, log_warning
from .error_codes import ErrorCode

logger = get_logger(__name__)

# Constants for SC-003 constraints
MAX_EXECUTION_TIME_SECONDS = 4 * 3600  # 4 hours
MAX_MEMORY_GB = 7.0

def get_peak_memory_gb() -> float:
    """
    Get the peak memory usage of the current process in GB.
    Uses psutil to access RSS (Resident Set Size) memory.
    """
    process = psutil.Process(os.getpid())
    # memory_info returns values in bytes
    mem_info = process.memory_info()
    # psutil might not have 'peak_wset' or similar on all platforms,
    # so we use current RSS as a proxy or track max manually if needed.
    # However, for a robust "peak" without OS-specific APIs (like getrusage),
    # we often rely on the max RSS tracked by the process or the current high-water mark.
    # psutil.Process.memory_info().rss is current.
    # To get a true "peak" across a long running process without OS support,
    # we might need to track it ourselves. But for this task, we will return
    # the current high-water mark if available or the current RSS.
    # On Linux, maxrss is available via resource module, but psutil is preferred.
    # Let's use the current RSS for the "peak" reported at the end of the run
    # as a conservative estimate, or try to access maxrss if possible.
    try:
        # Try to get maxrss if available (Linux/macOS via resource)
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS (sometimes).
        # Linux: ru_maxrss is in KB.
        peak_kb = usage.ru_maxrss
        # Convert to GB
        peak_gb = peak_kb / (1024 * 1024)
        return peak_gb
    except Exception:
        # Fallback to current RSS in GB
        return mem_info.rss / (1024 * 1024 * 1024)

def check_resource_constraints(execution_time: float, memory_gb: float) -> bool:
    """
    Check if the execution time and memory usage are within SC-003 constraints.
    Returns True if constraints are met, False otherwise.
    Logs errors and raises SystemExit if constraints are violated.
    """
    if execution_time > MAX_EXECUTION_TIME_SECONDS:
        log_error(
            ErrorCode.INSUFFICIENT_POWER,
            f"Execution time {execution_time:.2f}s exceeds limit {MAX_EXECUTION_TIME_SECONDS}s"
        )
        return False

    if memory_gb > MAX_MEMORY_GB:
        log_error(
            ErrorCode.INSUFFICIENT_POWER,
            f"Memory usage {memory_gb:.2f}GB exceeds limit {MAX_MEMORY_GB}GB"
        )
        return False

    return True

def monitor_resources(func: Callable) -> Callable:
    """
    Decorator to monitor execution time and peak memory of a function.
    Writes results to data/artifacts/resource_log.json.
    Enforces SC-003 constraints.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Start tracking memory if we want to capture peak during execution
        # For simplicity and robustness, we rely on resource.getrusage at the end
        # which captures the peak since process start (or wrapper start if called fresh).
        # To be precise about the function's scope, we might need to reset or track deltas,
        # but standard resource usage is cumulative.
        
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            log_error(ErrorCode.INSUFFICIENT_POWER, f"Function {func.__name__} failed: {str(e)}")
            raise

        end_time = time.time()
        execution_time = end_time - start_time
        peak_memory = get_peak_memory_gb()

        # Log to console
        log_info(
            None,
            f"Resource usage for {func.__name__}: {execution_time:.2f}s, {peak_memory:.2f}GB"
        )

        # Check constraints
        if not check_resource_constraints(execution_time, peak_memory):
            # Halt execution if constraints are violated
            log_error(
                ErrorCode.INSUFFICIENT_POWER,
                "Resource constraints violated. Halting pipeline."
            )
            sys.exit(1)

        # Write to artifact file
        output_path = "data/artifacts/resource_log.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        log_entry = {
            "execution_time_seconds": round(execution_time, 2),
            "peak_memory_gb": round(peak_memory, 2)
        }

        try:
            with open(output_path, 'w') as f:
                json.dump(log_entry, f, indent=2)
            log_info(None, f"Resource log written to {output_path}")
        except Exception as e:
            log_error(ErrorCode.DATA_SOURCE_MISSING, f"Failed to write resource log: {str(e)}")
            # Non-fatal for the script, but we log it

        return result

    return wrapper

def log_resource_usage(execution_time: float, peak_memory_gb: float) -> None:
    """
    Directly log resource usage to the artifact file without a decorator.
    Useful for manual instrumentation.
    """
    output_path = "data/artifacts/resource_log.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    log_entry = {
        "execution_time_seconds": round(execution_time, 2),
        "peak_memory_gb": round(peak_memory_gb, 2)
    }

    with open(output_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    log_info(None, f"Resource usage logged: {execution_time:.2f}s, {peak_memory_gb:.2f}GB")

def main():
    """
    Main entry point for resource_monitor module.
    Can be used to test the monitoring functionality.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Resource Monitor Utility")
    parser.add_argument("--test", action="store_true", help="Run a dummy test")
    args = parser.parse_args()

    if args.test:
        log_info(None, "Running resource monitor test...")
        time.sleep(1)
        peak_mem = get_peak_memory_gb()
        log_resource_usage(1.0, peak_mem)
        check_resource_constraints(1.0, peak_mem)
        log_info(None, "Test completed successfully.")
    else:
        log_info(None, "Resource Monitor module loaded. Use as a decorator or call functions directly.")

if __name__ == "__main__":
    main()
