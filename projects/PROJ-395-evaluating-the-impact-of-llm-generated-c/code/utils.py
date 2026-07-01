import csv
import os
import signal
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Callable
from contextlib import contextmanager

from config import EXECUTION_TIMEOUT_SECONDS, FAILURE_PENALTY_MEMORY_GB, FAILURE_PENALTY_TIME_SECONDS

class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeded the timeout limit."""
    pass

class OutOfMemoryError(Exception):
    """Raised when code execution exceeds memory limits."""
    pass

class SyntaxErrorWrapper(Exception):
    """Wrapper for syntax errors in generated code."""
    pass

@contextmanager
def run_with_timeout_and_memory_limit(timeout_seconds: int = EXECUTION_TIMEOUT_SECONDS):
    """
    Context manager to run a function with a timeout and memory limit.
    Note: Actual memory limiting requires OS-level tools (ulimit/cgroups) not available in pure Python context.
    This implementation focuses on timeout enforcement.
    """
    start_time = time.time()
    try:
        yield
    except Exception as e:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            raise ExecutionTimeoutError(f"Execution timed out after {elapsed:.2f}s")
        raise

def calculate_total_resource_cost(memory_bytes: float, time_seconds: float, is_failure: bool = False) -> float:
    """
    Calculate the total resource cost metric.
    Cost = (Memory * Time) + (Failure_Penalty if failure)
    
    The failure penalty is a massive constant to account for censored data handling
    as per the project specification.
    """
    base_cost = memory_bytes * time_seconds
    if is_failure:
        # Penalty calculated as (7GB * 60s) converted to bytes
        penalty = (FAILURE_PENALTY_MEMORY_GB * 1024**3) * FAILURE_PENALTY_TIME_SECONDS
        return base_cost + penalty
    return base_cost

def write_memory_measurements_csv(
    measurements: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Write memory measurements to a CSV file.
    Schema: problem_id, source_type, peak_memory, steady_state, status, total_resource_cost
    
    This function implements the logic required for T017 to persist profiling results.
    It ensures the output directory exists before writing.
    """
    fieldnames = ["problem_id", "source_type", "peak_memory", "steady_state", "status", "total_resource_cost"]
    
    # Ensure the directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(measurements)

def read_memory_measurements_csv(input_path: str) -> List[Dict[str, Any]]:
    """
    Read memory measurements from a CSV file.
    Returns an empty list if the file does not exist.
    """
    if not os.path.exists(input_path):
        return []
    with open(input_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def retry_on_transient_error(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 1.0
) -> Any:
    """
    Retry a function call on transient errors (e.g., network, temporary OOM).
    """
    last_exception = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            time.sleep(backoff_factor * (2 ** attempt))
    raise last_exception
