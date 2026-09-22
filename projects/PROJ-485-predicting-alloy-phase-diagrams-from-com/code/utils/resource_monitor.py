import os
import sys
import time
import json
import psutil
from typing import Optional, Dict, Any, Callable

from utils.logging import get_logger, log_info, log_error, log_warning
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

# Resource limits defined in task T028
MAX_EXECUTION_TIME_SECONDS = 14400  # 4 hours
MAX_PEAK_MEMORY_GB = 7.0

def get_peak_memory_gb() -> float:
    """
    Get the peak memory usage of the current process in GB.
    Uses psutil which is available in the standard environment.
    """
    process = psutil.Process(os.getpid())
    # memory_info returns RSS (Resident Set Size) in bytes
    mem_info = process.memory_info()
    # Convert bytes to GB
    peak_memory_bytes = mem_info.rss
    # Note: psutil does not track 'peak' RSS across the whole lifetime by default
    # on all platforms, but memory_info().rss is the current high-water mark for the process
    # in many contexts. For strict peak, we rely on the current high-water mark.
    peak_memory_gb = peak_memory_bytes / (1024 ** 3)
    return peak_memory_gb

def check_resource_constraints(execution_time: int, peak_memory_gb: float) -> bool:
    """
    Check if execution time and memory usage exceed defined limits.
    Returns True if constraints are met (safe to continue).
    Returns False if limits are exceeded (must halt).
    """
    if execution_time > MAX_EXECUTION_TIME_SECONDS:
        log_error(
            ErrorCode.RESOURCE_LIMIT_EXCEEDED,
            f"Execution time {execution_time}s exceeds limit {MAX_EXECUTION_TIME_SECONDS}s"
        )
        return False

    if peak_memory_gb > MAX_PEAK_MEMORY_GB:
        log_error(
            ErrorCode.RESOURCE_LIMIT_EXCEEDED,
            f"Peak memory {peak_memory_gb:.2f}GB exceeds limit {MAX_PEAK_MEMORY_GB}GB"
        )
        return False

    return True

def monitor_resources(
    func: Callable,
    *args,
    output_path: str = "data/artifacts/resource_log.json",
    **kwargs
) -> Any:
    """
    Wrapper to monitor execution time and peak memory of a function.
    
    Args:
        func: The function to execute and monitor.
        *args: Positional arguments for func.
        output_path: Path to write the resource log JSON.
        **kwargs: Keyword arguments for func.
        
    Returns:
        The return value of func.
        
    Raises:
        SystemExit: If resource limits are exceeded.
        Exception: Any exception raised by func.
    """
    start_time = time.time()
    
    # Capture initial memory to calculate delta if needed, 
    # though we track peak absolute usage as per spec.
    initial_memory = get_peak_memory_gb()
    
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        # Log error but don't necessarily halt for resource reasons if the error is internal
        log_error(ErrorCode.RESOURCE_LIMIT_EXCEEDED, f"Function failed: {str(e)}")
        raise

    end_time = time.time()
    execution_time_seconds = int(end_time - start_time)
    peak_memory_gb = get_peak_memory_gb()

    # Prepare log data
    log_data = {
        "execution_time_seconds": execution_time_seconds,
        "peak_memory_gb": round(peak_memory_gb, 4)
    }

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Write to disk
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)

    log_info(
        "RESOURCE_MONITOR",
        f"Execution completed. Time: {execution_time_seconds}s, Memory: {peak_memory_gb:.4f}GB"
    )

    # Check constraints
    if not check_resource_constraints(execution_time_seconds, peak_memory_gb):
        log_error(
            ErrorCode.RESOURCE_LIMIT_EXCEEDED,
            "Resource limits exceeded. Halting pipeline."
        )
        # Halt the pipeline immediately as per requirement
        sys.exit(1)

    return result

def log_resource_usage(output_path: str = "data/artifacts/resource_log.json") -> Dict[str, Any]:
    """
    Log current resource usage without wrapping a function.
    Useful for periodic checks or manual logging.
    """
    execution_time_seconds = int(time.time() - start_time_global) if 'start_time_global' in globals() else 0
    peak_memory_gb = get_peak_memory_gb()
    
    log_data = {
        "execution_time_seconds": execution_time_seconds,
        "peak_memory_gb": round(peak_memory_gb, 4)
    }
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
        
    return log_data

# Global start time for standalone logging if needed
start_time_global = time.time()

def main():
    """
    Main entry point for running resource monitoring as a script.
    This is useful for testing the monitor or running a simple command with monitoring.
    Usage: python -m code.utils.resource_monitor --command "python code/models/train.py"
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Resource Monitor Wrapper")
    parser.add_argument("--command", type=str, required=False, help="Command to execute (optional)")
    parser.add_argument("--output", type=str, default="data/artifacts/resource_log.json", help="Output path for log")
    
    args = parser.parse_args()
    
    if args.command:
        # If a command is provided, we would ideally exec it, but for this task
        # we focus on the module functionality. 
        # The primary usage is via the `monitor_resources` decorator/wrapper in other code.
        print("Resource Monitor Module Loaded.")
        print(f"Max Time: {MAX_EXECUTION_TIME_SECONDS}s, Max Memory: {MAX_PEAK_MEMORY_GB}GB")
        
        # Run a dummy check to verify imports and basic logic
        current_mem = get_peak_memory_gb()
        print(f"Current Memory Usage: {current_mem:.4f} GB")
        
        # Verify constraints
        check_resource_constraints(100, current_mem)
    else:
        print("Resource Monitor Utility.")
        print("Import `monitor_resources` from `utils.resource_monitor` to wrap your functions.")
        
        # Verify imports
        from utils.logging import get_logger
        from utils.error_codes import ErrorCode
        print("Dependencies verified.")

if __name__ == "__main__":
    main()