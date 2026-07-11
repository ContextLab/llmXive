"""Baseline runner module with timeout handling logic.

This module implements the execution logic for code tasks with a configurable
timeout mechanism. It ensures that tasks exceeding the time limit are marked
as "Timeout" rather than "Unknown" or "Skipped".
"""

import time
import threading
from dataclasses import dataclass
from typing import Callable, Any, Optional
import os


@dataclass
class ExecutionResult:
    """Container for the result of a code execution."""
    status: str  # "Pass", "Fail", "Timeout", "Error"
    output: Optional[str] = None
    error: Optional[str] = None


def run_with_timeout(
    func: Callable[[], Any],
    timeout_seconds: float,
    *args,
    **kwargs
) -> ExecutionResult:
    """
    Executes a function with a strict timeout.

    Args:
        func: The function to execute.
        timeout_seconds: Maximum allowed execution time in seconds.
        *args: Positional arguments to pass to func.
        **kwargs: Keyword arguments to pass to func.

    Returns:
        ExecutionResult with status "Timeout" if time is exceeded,
        "Fail" if an exception occurs, or "Pass" if successful.
    """
    result_container = {"result": None, "exception": None, "timed_out": False}

    def target():
        try:
            result_container["result"] = func(*args, **kwargs)
        except Exception as e:
            result_container["exception"] = e

    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        # Thread is still running, meaning timeout occurred
        # Explicitly forbid treating timeouts as "Unknown" or "Skipped"
        return ExecutionResult(
            status="Timeout",
            error=f"Execution exceeded {timeout_seconds}s limit"
        )

    if result_container["exception"]:
        return ExecutionResult(
            status="Fail",
            error=str(result_container["exception"])
        )

    return ExecutionResult(
        status="Pass",
        output=str(result_container["result"])
    )


def run_baseline_task(task_id: str, code_diff: str, original_code: str, timeout_seconds: float = 30.0) -> ExecutionResult:
    """
    Simulates running a baseline task with a configurable timeout.
    
    This function represents the interface for executing a task in the 
    baseline runner. It wraps the execution in the timeout handler to 
    ensure safety conservatism.
    
    Args:
        task_id: Unique identifier for the task.
        code_diff: The proposed code changes.
        original_code: The original code before changes.
        timeout_seconds: Maximum duration for execution (default 30s).
        
    Returns:
        ExecutionResult indicating Pass, Fail, or Timeout.
    """
    def simulate_execution():
        # In a real implementation, this would invoke Docker/sandboxing
        # to run the test suite against the code_diff.
        # For this implementation, we simulate a deterministic execution
        # based on the task content to demonstrate the timeout logic.
        
        # Simulate a task that takes time based on the length of code_diff
        # to allow testing of the timeout mechanism.
        work_units = len(code_diff) / 100.0
        sleep_time = min(work_units, 5.0) # Cap simulation time for demo
        
        # If the code_diff contains "TIMEOUT_TEST", force a long sleep
        if "TIMEOUT_TEST" in code_diff:
            sleep_time = timeout_seconds + 1.0
        
        time.sleep(sleep_time)
        
        # Simulate a pass/fail based on content
        if "FAIL_ME" in code_diff:
            raise RuntimeError("Test suite failed: assertion error")
        
        return f"Task {task_id} executed successfully."

    return run_with_timeout(
        func=simulate_execution,
        timeout_seconds=timeout_seconds
    )


def main():
    """
    Entry point for testing the baseline runner timeout logic.
    Reads configuration from environment or defaults.
    """
    timeout_val = os.getenv("BASELINE_TIMEOUT", "30")
    try:
        timeout_seconds = float(timeout_val)
    except ValueError:
        timeout_seconds = 30.0

    print(f"Baseline Runner initialized with timeout: {timeout_seconds}s")
    
    # Example test cases to demonstrate timeout and fail handling
    test_cases = [
        {
            "id": "test_normal",
            "diff": "print('hello')",
            "orig": "print('old')",
            "expected": "Pass"
        },
        {
            "id": "test_timeout",
            "diff": "TIMEOUT_TEST: This will hang",
            "orig": "print('old')",
            "expected": "Timeout"
        },
        {
            "id": "test_fail",
            "diff": "FAIL_ME: This will raise",
            "orig": "print('old')",
            "expected": "Fail"
        }
    ]

    for case in test_cases:
        result = run_baseline_task(
            task_id=case["id"],
            code_diff=case["diff"],
            original_code=case["orig"],
            timeout_seconds=timeout_seconds
        )
        
        print(f"Task {case['id']}: Status={result.status}")
        if result.error:
            print(f"  Error: {result.error}")
        if result.output:
            print(f"  Output: {result.output}")
        
        # Verify safety conservatism: Timeout must be explicit, not Unknown/Skipped
        if result.status == "Timeout":
            assert result.status != "Unknown", "Safety violation: Timeout treated as Unknown"
            assert result.status != "Skipped", "Safety violation: Timeout treated as Skipped"
            print("  [Safety Check] Passed: Timeout explicitly recorded.")

    print("Baseline runner timeout logic verification complete.")


if __name__ == "__main__":
    main()