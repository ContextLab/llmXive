import csv
import os
import signal
import subprocess
import sys
import time
from typing import Optional, Tuple, Callable, Any
from contextlib import contextmanager
import tempfile
import traceback

# Configuration constants
EXECUTION_TIMEOUT_SECONDS = 60
MEMORY_LIMIT_GB = 7
MAX_RETRIES = 3
RETRY_DELAY = 1.0

class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds the timeout limit."""
    pass

class OutOfMemoryError(Exception):
    """Raised when code execution exceeds memory limits."""
    pass

class SyntaxErrorWrapper(Exception):
    """Wrapper for syntax errors in executed code."""
    pass

@contextmanager
def timeout_context(seconds: int):
    """Context manager to enforce execution timeout."""
    def signal_handler(signum, frame):
        raise ExecutionTimeoutError(f"Execution timed out after {seconds} seconds")
    
    # Set the signal handler
    original_handler = signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the original handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)

def run_with_timeout_and_memory_limit(
    script_path: str,
    timeout_sec: int = EXECUTION_TIMEOUT_SECONDS,
    memory_limit_gb: int = MEMORY_LIMIT_GB
) -> subprocess.CompletedProcess:
    """
    Run a Python script with timeout and memory limits.
    
    Args:
        script_path: Path to the Python script to execute
        timeout_sec: Maximum execution time in seconds
        memory_limit_gb: Maximum memory usage in GB
        
    Returns:
        CompletedProcess instance
        
    Raises:
        ExecutionTimeoutError: If execution exceeds timeout
        OutOfMemoryError: If execution exceeds memory limit
        SyntaxErrorWrapper: If there's a syntax error in the code
    """
    # Convert memory limit to bytes for ulimit
    memory_limit_bytes = memory_limit_gb * 1024 * 1024 * 1024
    
    try:
        with timeout_context(timeout_sec):
            # Run the script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=timeout_sec
            )
            
            # Check for syntax errors
            if "SyntaxError" in result.stderr or "Syntax error" in result.stderr.lower():
                raise SyntaxErrorWrapper(f"Syntax error in code: {result.stderr}")
            
            # Check for memory errors
            if "MemoryError" in result.stderr or "out of memory" in result.stderr.lower():
                raise OutOfMemoryError(f"Out of memory: {result.stderr}")
            
            return result
            
    except subprocess.TimeoutExpired:
        raise ExecutionTimeoutError(f"Execution timed out after {timeout_sec} seconds")
    except SyntaxErrorWrapper:
        raise
    except OutOfMemoryError:
        raise
    except Exception as e:
        # Re-raise as our custom exceptions if appropriate
        if "timeout" in str(e).lower():
            raise ExecutionTimeoutError(str(e))
        elif "memory" in str(e).lower():
            raise OutOfMemoryError(str(e))
        else:
            raise

def execute_code_safely(
    code: str,
    timeout_sec: int = EXECUTION_TIMEOUT_SECONDS,
    memory_limit_gb: int = MEMORY_LIMIT_GB
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Execute code safely with timeout and memory limits.
    
    Args:
        code: Python code string to execute
        timeout_sec: Maximum execution time
        memory_limit_gb: Maximum memory usage
        
    Returns:
        Tuple of (success, stdout, stderr)
    """
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = run_with_timeout_and_memory_limit(
            temp_path,
            timeout_sec=timeout_sec,
            memory_limit_gb=memory_limit_gb
        )
        return (True, result.stdout, result.stderr)
    except ExecutionTimeoutError as e:
        return (False, None, str(e))
    except OutOfMemoryError as e:
        return (False, None, str(e))
    except SyntaxErrorWrapper as e:
        return (False, None, str(e))
    except Exception as e:
        return (False, None, f"Unexpected error: {str(e)}")
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def retry_on_transient_error(
    func: Callable,
    *args,
    max_retries: int = MAX_RETRIES,
    delay: float = RETRY_DELAY,
    **kwargs
) -> Any:
    """
    Retry a function call on transient errors.
    
    Args:
        func: Function to call
        *args: Positional arguments to pass to func
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        Result of func call
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except (ExecutionTimeoutError, OutOfMemoryError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(delay)
                continue
            else:
                raise
        except Exception as e:
            # For non-transient errors, don't retry
            raise
    
    raise last_exception

def calculate_total_resource_cost(
    memory_bytes: Optional[float],
    time_seconds: float,
    status: str
) -> float:
    """
    Calculate total resource cost for a code execution.
    
    For successful executions: Memory * Time
    For failed executions (timeout/OOM): 7GB * 60s (penalty)
    
    Args:
        memory_bytes: Peak memory usage in bytes (None for failures)
        time_seconds: Execution time in seconds
        status: Execution status ('success', 'timeout', 'oom', etc.)
        
    Returns:
        Total resource cost in GB*seconds
    """
    # Constants for penalty calculation
    PENALTY_MEMORY_GB = 7.0
    PENALTY_TIME_SECONDS = 60.0
    
    if status in ['timeout', 'oom']:
        # Apply penalty for failures
        return PENALTY_MEMORY_GB * PENALTY_TIME_SECONDS
    elif status == 'success' and memory_bytes is not None:
        # Convert bytes to GB and calculate cost
        memory_gb = memory_bytes / (1024 ** 3)
        return memory_gb * time_seconds
    else:
        # For other cases (syntax errors, etc.), return 0 or a small penalty
        return 0.0

def write_memory_measurements_csv(
    measurements: list,
    output_path: str
) -> None:
    """
    Write memory measurements to a CSV file.
    
    Args:
        measurements: List of measurement dictionaries
        output_path: Path to output CSV file
    """
    if not measurements:
        # Create empty file with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'problem_id',
                'source_type',
                'peak_memory',
                'steady_state',
                'status',
                'total_resource_cost'
            ])
        return
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'problem_id',
            'source_type',
            'peak_memory',
            'steady_state',
            'status',
            'total_resource_cost'
        ])
        writer.writeheader()
        writer.writerows(measurements)

def read_memory_measurements_csv(input_path: str) -> list:
    """
    Read memory measurements from a CSV file.
    
    Args:
        input_path: Path to input CSV file
        
    Returns:
        List of measurement dictionaries
    """
    measurements = []
    
    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            if row['peak_memory']:
                row['peak_memory'] = float(row['peak_memory'])
            if row['steady_state']:
                row['steady_state'] = float(row['steady_state'])
            if row['total_resource_cost']:
                row['total_resource_cost'] = float(row['total_resource_cost'])
            
            measurements.append(row)
    
    return measurements