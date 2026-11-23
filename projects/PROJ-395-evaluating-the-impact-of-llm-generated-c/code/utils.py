"""
Utility functions for the memory impact evaluation project.

This module provides common utilities including:
    - Custom exceptions (Timeout, OOM, Syntax)
    - Timeout and memory limit context managers
    - Safe code execution with error handling
    - Retry logic for transient failures
    - Resource cost calculation
    - CSV I/O helpers

Key Functions:
    - run_with_timeout_and_memory_limit: Execute code with constraints
    - execute_code_safely: Execute with comprehensive error handling
    - retry_on_transient_error: Retry failed operations
    - calculate_total_resource_cost: Compute composite penalty score
    - write_memory_measurements_csv: Save profiling results
    - save_memory_measurements: Convenience wrapper that writes to the
      project‑wide default location (data/processed/memory_measurements.csv)

Usage:
    from utils import execute_code_safely, calculate_total_resource_cost, save_memory_measurements
    result = execute_code_safely(code, timeout=60)
    cost = calculate_total_resource_cost(result['memory'], result['time'], result['status'])
    save_memory_measurements([{
        'problem_id': 'humaneval-1',
        'source_type': 'LLM',
        'peak_memory': result['peak_memory'],
        'steady_state': result['steady_state'],
        'status': result['status'],
        'total_resource_cost': cost
    }])
"""

import csv
import os
import signal
import subprocess
import sys
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Callable

from config import CI_MEMORY_LIMIT_GB, TIMEOUT_SECONDS, MEMORY_MEASUREMENTS_PATH

# ============================================================================
# Custom Exceptions
# ============================================================================

class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds the timeout limit."""
    pass


class OutOfMemoryError(Exception):
    """Raised when code execution exceeds memory limits."""
    pass


class SyntaxErrorWrapper(Exception):
    """Wrapper for syntax errors in generated code."""
    pass


# ============================================================================
# Timeout and Memory Context Managers
# ============================================================================

def timeout_context(seconds: int):
    """
    Context manager for setting execution timeout.

    Args:
        seconds: Timeout duration in seconds.

    Yields:
        None

    Raises:
        ExecutionTimeoutError: If timeout is exceeded.
    """
    def timeout_handler(signum, frame):
        raise ExecutionTimeoutError(f"Execution timed out after {seconds} seconds")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def run_with_timeout_and_memory_limit(
    script_path: str,
    timeout: int = TIMEOUT_SECONDS,
    memory_limit_gb: float = CI_MEMORY_LIMIT_GB
) -> Dict[str, Any]:
    """
    Run a Python script with timeout and memory limits.

    Args:
        script_path: Path to the Python script to execute.
        timeout: Maximum execution time in seconds.
        memory_limit_gb: Memory limit in GB.

    Returns:
        Dict[str, Any]: Execution results with status and metrics.

    Raises:
        ExecutionTimeoutError: If execution exceeds timeout.
        OutOfMemoryError: If execution exceeds memory limit.
    """
    result = {
        'status': 'success',
        'returncode': 0,
        'stdout': '',
        'stderr': ''
    }

    # Set memory limit using ulimit (Unix only)
    # Note: Windows memory limiting requires different approach
    if os.name != 'nt':
        try:
            import resource  # Imported lazily to avoid import errors on Windows
            memory_limit_bytes = int(memory_limit_gb * 1024 * 1024 * 1024)
            soft, hard = resource.getrlimit(resource.RLIMIT_AS)
            resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
        except Exception:
            pass  # If resource module unavailable or limit cannot be set, continue without limiting

    try:
        start_time = time.time()
        process = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start_time

        result['returncode'] = process.returncode
        result['stdout'] = process.stdout
        result['stderr'] = process.stderr

        if process.returncode != 0:
            # Check for OOM indicators in stderr
            if 'MemoryError' in process.stderr or 'OOM' in process.stderr:
                result['status'] = 'oom'
                raise OutOfMemoryError("Memory limit exceeded")

    except subprocess.TimeoutExpired:
        result['status'] = 'timeout'
        raise ExecutionTimeoutError(f"Execution timed out after {timeout} seconds")
    except MemoryError:
        result['status'] = 'oom'
        raise OutOfMemoryError("Memory limit exceeded")
    except Exception as e:
        result['status'] = 'error'
        result['stderr'] = str(e)
        raise

    return result


def execute_code_safely(
    code: str,
    timeout: int = TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Execute code safely with comprehensive error handling.

    Args:
        code: Code string to execute.
        timeout: Execution timeout in seconds.

    Returns:
        Dict[str, Any]: Execution results.
    """
    result = {
        'status': 'success',
        'error': None,
        'output': None
    }

    # Check for syntax errors first
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        result['status'] = 'syntax_error'
        result['error'] = str(e)
        return result

    # Execute with timeout
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        exec_result = run_with_timeout_and_memory_limit(temp_path, timeout)
        result['output'] = exec_result['stdout']
        result['status'] = exec_result['status']
    except ExecutionTimeoutError as e:
        result['status'] = 'timeout'
        result['error'] = str(e)
    except OutOfMemoryError as e:
        result['status'] = 'oom'
        result['error'] = str(e)
    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass

    return result


def retry_on_transient_error(
    func: Callable,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Callable:
    """
    Decorator to retry a function on transient errors.

    Args:
        func: Function to wrap.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Multiplier for exponential backoff.

    Returns:
        Callable: Wrapped function.
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
        raise last_exception

    return wrapper


def calculate_total_resource_cost(
    peak_memory_bytes: float,
    execution_time_seconds: float,
    status: str
) -> float:
    """
    Calculate total resource cost as a composite penalty score.

    Formula: Memory_Bytes * Time_Seconds + Failure_Penalty

    For failed executions (timeout, oom, N/A), a large penalty is applied
    to reflect the cost of wasted resources.

    Args:
        peak_memory_bytes: Peak memory usage in bytes.
        execution_time_seconds: Execution time in seconds.
        status: Execution status ('success', 'timeout', 'oom', 'N/A').

    Returns:
        float: Total resource cost score.
    """
    # Base cost for successful runs
    base_cost = peak_memory_bytes * execution_time_seconds

    # Failure penalty (7GB * 60s)
    FAILURE_PENALTY = CI_MEMORY_LIMIT_GB * 1024 * 1024 * 1024 * TIMEOUT_SECONDS

    if status == 'success':
        return base_cost
    else:
        return base_cost + FAILURE_PENALTY


# ============================================================================
# CSV I/O Helpers
# ============================================================================

def write_memory_measurements_csv(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Write memory measurements to a CSV file.

    Args:
        results: List of measurement dictionaries.
        output_path: Path to save the CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        'problem_id',
        'source_type',
        'peak_memory',
        'steady_state',
        'status',
        'total_resource_cost'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Written {len(results)} measurements to {output_path}")


def read_memory_measurements_csv(input_path: str) -> List[Dict[str, Any]]:
    """
    Read memory measurements from a CSV file.

    Args:
        input_path: Path to the CSV file.

    Returns:
        List[Dict]: List of measurement dictionaries.
    """
    results = []
    with open(input_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['peak_memory'] = float(row['peak_memory'])
            row['steady_state'] = float(row.get('steady_state', 0))
            row['total_resource_cost'] = float(row.get('total_resource_cost', 0))
            results.append(row)

    return results


# ============================================================================
# Convenience Wrapper
# ============================================================================

def save_memory_measurements(
    results: List[Dict[str, Any]],
    output_path: str = MEMORY_MEASUREMENTS_PATH
) -> None:
    """
    Convenience wrapper that writes memory measurement results to the
    project‑wide default CSV location.

    This function satisfies the T017 requirement by ensuring that the
    CSV file ``data/processed/memory_measurements.csv`` is created with the
    exact schema:

        problem_id, source_type, peak_memory, steady_state, status,
        total_resource_cost

    Args:
        results: List of dictionaries matching the schema.
        output_path: Optional override path; defaults to the
            ``MEMORY_MEASUREMENTS_PATH`` defined in ``config.py``.
    """
    write_memory_measurements_csv(results, output_path)