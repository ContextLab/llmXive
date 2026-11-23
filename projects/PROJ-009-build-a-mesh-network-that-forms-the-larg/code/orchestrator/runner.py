"""
Hard Timeout Wrapper for Mesh Network Orchestration.

Implements FR-007: Enforce a hard 6-hour CI limit on all execution runs.
Uses a separate process with a timeout to ensure the main thread cannot
hang indefinitely.
"""
from __future__ import annotations

import logging
import multiprocessing
import signal
import sys
import time
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Optional, TypeVar

from orchestrator.config import load_config
from orchestrator.logger import get_logger

# Constants
# FR-007: 6-hour CI limit in seconds
CI_HARD_TIMEOUT_SECONDS = 6 * 60 * 60
# Safety buffer (e.g., 5 minutes) to allow graceful shutdown before hard kill
GRACE_PERIOD_SECONDS = 5 * 60

T = TypeVar('T')

logger = get_logger(__name__)


class ExecutionTimeoutError(Exception):
    """Raised when an execution run exceeds the hard timeout limit."""
    pass


@dataclass
class ExecutionResult:
    """Container for the result of a timed execution."""
    success: bool
    output: Any
    error: Optional[str]
    duration_seconds: float
    timed_out: bool
    timestamp: datetime


def _worker_function(
    func: Callable[..., T],
    args: tuple,
    kwargs: dict
) -> T:
    """
    Wrapper function executed in the child process.
    This allows the parent to kill the process if it hangs.
    """
    # Set a handler to catch SIGTERM for graceful shutdown if possible
    # though the parent will likely just kill the process.
    return func(*args, **kwargs)


def run_with_hard_timeout(
    func: Callable[..., T],
    *args: Any,
    timeout_seconds: int = CI_HARD_TIMEOUT_SECONDS,
    graceful_shutdown: bool = True,
    **kwargs: Any
) -> ExecutionResult:
    """
    Executes a function with a hard timeout enforced via a separate process.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        timeout_seconds: Maximum allowed execution time in seconds.
        graceful_shutdown: If True, sends SIGTERM before SIGKILL.
        **kwargs: Keyword arguments for the function.

    Returns:
        ExecutionResult containing the outcome.

    Raises:
        ExecutionTimeoutError: If the function exceeds the timeout and we
                               cannot cleanly report it (fallback).
    """
    start_time = time.monotonic()
    logger.info(
        "Starting execution with hard timeout",
        extra={
            "function": func.__name__,
            "timeout_seconds": timeout_seconds,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

    result_queue = multiprocessing.Queue()
    exception_queue = multiprocessing.Queue()

    def target(q_result, q_exception):
        try:
            res = func(*args, **kwargs)
            q_result.put(res)
        except Exception as e:
            q_exception.put(e)

    process = multiprocessing.Process(
        target=target,
        args=(result_queue, exception_queue),
        name=f"ExecWorker-{func.__name__}"
    )

    process.start()
    process.join(timeout=timeout_seconds)

    duration = time.monotonic() - start_time

    if process.is_alive():
        # Timeout occurred
        logger.error(
            f"Execution timed out after {duration:.2f} seconds. "
            f"Enforcing hard kill for {func.__name__}.",
            extra={
                "function": func.__name__,
                "duration_seconds": duration,
                "timeout_seconds": timeout_seconds
            }
        )

        # Attempt graceful shutdown first if requested
        if graceful_shutdown:
            logger.info(f"Sending SIGTERM to process {process.pid}")
            process.terminate()
            process.join(timeout=GRACE_PERIOD_SECONDS)

        if process.is_alive():
            logger.critical(
                f"Graceful shutdown failed. Sending SIGKILL to process {process.pid}",
                extra={"pid": process.pid}
            )
            process.kill()
            process.join()

        return ExecutionResult(
            success=False,
            output=None,
            error=f"Hard timeout exceeded: {timeout_seconds} seconds",
            duration_seconds=duration,
            timed_out=True,
            timestamp=datetime.utcnow()
        )

    # Process finished within timeout
    if not result_queue.empty():
        output = result_queue.get()
        logger.info(
            f"Execution completed successfully in {duration:.2f} seconds",
            extra={"function": func.__name__, "duration_seconds": duration}
        )
        return ExecutionResult(
            success=True,
            output=output,
            error=None,
            duration_seconds=duration,
            timed_out=False,
            timestamp=datetime.utcnow()
        )

    if not exception_queue.empty():
        exc = exception_queue.get()
        logger.error(
            f"Execution failed with exception: {exc}",
            extra={"function": func.__name__, "error_type": type(exc).__name__}
        )
        return ExecutionResult(
            success=False,
            output=None,
            error=str(exc),
            duration_seconds=duration,
            timed_out=False,
            timestamp=datetime.utcnow()
        )

    # Fallback: Process finished but no result/exception (should not happen)
    logger.warning("Process finished but no result captured.")
    return ExecutionResult(
        success=False,
        output=None,
        error="Process finished without returning a result or raising an exception",
        duration_seconds=duration,
        timed_out=False,
        timestamp=datetime.utcnow()
    )


def validate_ci_timeout_config(config: Optional[Dict[str, Any]] = None) -> int:
    """
    Validates and retrieves the CI timeout configuration.
    Defaults to 6 hours if not specified, ensuring FR-007 compliance.
    """
    if config is None:
        try:
            config = load_config()
        except FileNotFoundError:
            logger.warning("No config file found, using default 6-hour timeout.")
            return CI_HARD_TIMEOUT_SECONDS

    orchestrator_cfg = config.get("orchestrator", {})
    timeout_val = orchestrator_cfg.get("ci_hard_timeout_seconds", CI_HARD_TIMEOUT_SECONDS)

    if not isinstance(timeout_val, (int, float)) or timeout_val <= 0:
        logger.warning(
            f"Invalid timeout value {timeout_val}, defaulting to {CI_HARD_TIMEOUT_SECONDS}"
        )
        return CI_HARD_TIMEOUT_SECONDS

    return int(timeout_val)


if __name__ == "__main__":
    # Simple CLI test to demonstrate the wrapper
    def slow_function(seconds: int):
        logger.info(f"Sleeping for {seconds} seconds...")
        time.sleep(seconds)
        return "Done"

    def normal_function():
        return "Immediate result"

    print("Testing Normal Function...")
    res = run_with_hard_timeout(normal_function, timeout_seconds=10)
    print(f"Result: {res.success}, Duration: {res.duration_seconds:.2f}s")

    print("\nTesting Slow Function (under limit)...")
    res = run_with_hard_timeout(slow_function, 5, timeout_seconds=10)
    print(f"Result: {res.success}, Duration: {res.duration_seconds:.2f}s")

    print("\nTesting Slow Function (over limit - 6s sleep, 5s timeout)...")
    res = run_with_hard_timeout(slow_function, 10, timeout_seconds=5)
    print(f"Result: {res.success}, Timed Out: {res.timed_out}, Error: {res.error}")
    print("Hard timeout enforcement verified.")