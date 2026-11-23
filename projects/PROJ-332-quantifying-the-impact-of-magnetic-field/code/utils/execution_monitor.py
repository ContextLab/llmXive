"""
Execution monitoring utilities for tracking pipeline runtime and enforcing timeouts.

This module provides functionality to monitor the execution time of pipeline
operations, enforce maximum execution limits, and generate execution reports.
It works in conjunction with the timeout utilities in limits.py.

Classes:
    TimeoutExceededError: Exception raised when execution time exceeds the limit.

Functions:
    time_execution: Decorator for timing function execution.
    verify_pipeline_execution_time: Check if total execution time is within limits.
    main: Entry point for running the execution monitor as a script.

Example:
    >>> from utils.execution_monitor import time_execution
    >>> @time_execution
    ... def long_task():
    ...     time.sleep(10)
    >>> long_task()
"""

import time
import json
import logging
import sys
import signal
from pathlib import Path
from functools import wraps
from typing import Optional, Callable, Any, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class TimeoutExceededError(Exception):
    """
    Exception raised when execution time exceeds the specified limit.

    This exception is used to signal that a pipeline operation or the entire
    pipeline has exceeded its allocated execution time.

    Attributes:
        message: Description of the timeout error.
        elapsed_time: Actual execution time in seconds.
        limit_time: Configured time limit in seconds.
    """

    def __init__(
        self,
        message: str = "Execution time limit exceeded",
        elapsed_time: float = 0.0,
        limit_time: float = 0.0
    ):
        self.message = message
        self.elapsed_time = elapsed_time
        self.limit_time = limit_time
        super().__init__(self.message)


def time_execution(
    func: Optional[Callable] = None,
    log_level: int = logging.INFO
) -> Callable:
    """
    Decorator that measures and logs the execution time of a function.

    This decorator wraps a function to automatically measure its execution time
    and log the result. It can also be used with arguments to customize behavior.

    Args:
        func: The function to decorate (when used without arguments).
        log_level: Logging level for the timing message (default INFO).

    Returns:
        The decorated function.

    Example:
        >>> @time_execution
        ... def process_data():
        ...     time.sleep(2)
        >>> process_data()
        # Logs: "Function 'process_data' completed in 2.03 seconds"
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.log(
                    log_level,
                    f"Function '{f.__name__}' completed in {elapsed:.3f} seconds"
                )
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.log(
                    log_level,
                    f"Function '{f.__name__}' failed after {elapsed:.3f} seconds: {e}"
                )
                raise

        return wrapper

    # Support both @time_execution and @time_execution()
    if func is not None:
        return decorator(func)
    return decorator


def verify_pipeline_execution_time(
    start_time: float,
    limit_seconds: int,
    strict: bool = True
) -> bool:
    """
    Verify that pipeline execution time is within the specified limit.

    Args:
        start_time: Timestamp when the pipeline started (from time.time()).
        limit_seconds: Maximum allowed execution time in seconds.
        strict: If True, raise an exception on failure. If False, return False.

    Returns:
        True if execution time is within limits, False otherwise.

    Raises:
        TimeoutExceededError: If strict=True and time limit is exceeded.
    """
    elapsed = time.time() - start_time

    if elapsed > limit_seconds:
        error_msg = (
            f"Pipeline execution time exceeded limit: {elapsed:.2f} seconds > "
            f"{limit_seconds} seconds"
        )
        if strict:
            raise TimeoutExceededError(
                message=error_msg,
                elapsed_time=elapsed,
                limit_time=limit_seconds
            )
        else:
            logger.warning(error_msg)
            return False

    logger.info(f"Pipeline execution time within limits: {elapsed:.2f} <= {limit_seconds} seconds")
    return True


def generate_execution_report(
    start_time: float,
    end_time: Optional[float] = None,
    status: str = "completed",
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Generate a JSON report of pipeline execution metrics.

    Args:
        start_time: Timestamp when the pipeline started.
        end_time: Timestamp when the pipeline ended. Defaults to current time.
        status: Execution status (e.g., "completed", "failed", "timeout").
        output_path: Optional path to save the report as a JSON file.

    Returns:
        Dictionary containing execution metrics.
    """
    if end_time is None:
        end_time = time.time()

    elapsed = end_time - start_time

    report = {
        'start_time': datetime.fromtimestamp(start_time).isoformat(),
        'end_time': datetime.fromtimestamp(end_time).isoformat(),
        'elapsed_seconds': elapsed,
        'status': status
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Execution report saved to {output_path}")

    return report


def main():
    """
    Main entry point for the execution monitor module.

    This function demonstrates the usage of the execution monitoring utilities
    with a simulated pipeline execution.
    """
    logger.info("Running utils/execution_monitor.py as a script (demo mode)")

    # Simulate pipeline execution
    start_time = time.time()
    limit_seconds = 300  # 5 minutes

    try:
        # Simulate work
        logger.info("Simulating pipeline execution...")
        for i in range(5):
            time.sleep(1)
            logger.info(f"Progress: {i+1}/5")

        # Verify execution time
        if verify_pipeline_execution_time(start_time, limit_seconds, strict=True):
            logger.info("Execution completed within time limit")

        # Generate report
        report = generate_execution_report(
            start_time=start_time,
            status="completed",
            output_path=Path('outputs/execution_report.json')
        )

        logger.info(f"Execution completed in {report['elapsed_seconds']:.2f} seconds")

    except TimeoutExceededError as e:
        logger.error(f"Execution timed out: {e.message}")
        generate_execution_report(
            start_time=start_time,
            status="timeout",
            output_path=Path('outputs/execution_report.json')
        )
        raise