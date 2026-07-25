"""
Memory and Time Monitor for Image Generation Pipeline.

This module provides utilities to monitor memory usage and enforce time limits
during the image generation process (User Story 2). It ensures that the
pipeline adheres to the CPU-only compute constraints defined in the project.

It integrates with the existing generation pipeline to:
1. Monitor RSS memory usage using `resource` (Unix) or `psutil` (Cross-platform).
2. Enforce a maximum time limit per batch.
3. Raise specific exceptions if limits are exceeded to halt the pipeline gracefully.
"""

import os
import sys
import time
import signal
from pathlib import Path
from typing import Optional, Callable, Any

# Try to import psutil for robust cross-platform memory monitoring
# If not available, fallback to resource (Unix only) or a simple mock
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    # Fallback for Unix systems
    try:
        import resource
        HAS_RESOURCE = True
    except ImportError:
        HAS_RESOURCE = False

# Project root relative path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class MemoryLimitExceededError(Exception):
    """Raised when memory usage exceeds the configured threshold."""
    pass


class TimeLimitExceededError(Exception):
    """Raised when the processing time exceeds the configured limit."""
    pass


def get_memory_usage_mb() -> float:
    """
    Returns the current memory usage of the process in Megabytes.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    elif HAS_RESOURCE:
        # rusage.ru_maxrss is in kilobytes on Linux/macOS
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0
    else:
        # Fallback: Return 0.0 if no method is available
        # This allows the code to run but monitoring will be ineffective
        return 0.0


def check_memory_limit(limit_mb: float) -> bool:
    """
    Checks if current memory usage is within the limit.

    Args:
        limit_mb: Maximum allowed memory in MB.

    Returns:
        True if within limit, False otherwise.
    """
    current = get_memory_usage_mb()
    return current <= limit_mb


def enforce_memory_limit(limit_mb: float):
    """
    Raises MemoryLimitExceededError if current memory usage exceeds limit.
    """
    if not check_memory_limit(limit_mb):
        current = get_memory_usage_mb()
        raise MemoryLimitExceededError(
            f"Memory limit exceeded: {current:.2f} MB > {limit_mb} MB"
        )


class TimeLimitEnforcer:
    """
    Context manager and utility to enforce a time limit on a block of code.
    """

    def __init__(self, limit_seconds: float, description: str = "Operation"):
        self.limit_seconds = limit_seconds
        self.description = description
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Always check on exit to ensure we don't exceed limits even if an exception occurred
        if self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed > self.limit_seconds:
                raise TimeLimitExceededError(
                    f"Time limit exceeded for {self.description}: "
                    f"{elapsed:.2f}s > {self.limit_seconds}s"
                )
        return False

    def check(self):
        """Check if the time limit has been exceeded since initialization."""
        if self.start_time is None:
            return
        elapsed = time.time() - self.start_time
        if elapsed > self.limit_seconds:
            raise TimeLimitExceededError(
                f"Time limit exceeded for {self.description}: "
                f"{elapsed:.2f}s > {self.limit_seconds}s"
            )


def monitor_batch_generation(
    batch_size: int,
    memory_limit_mb: float = 8192.0,  # Default 8GB
    time_limit_seconds: float = 300.0   # Default 5 minutes per batch
) -> Callable:
    """
    Decorator to monitor memory and time for a batch generation function.

    Args:
        batch_size: Expected number of items in the batch.
        memory_limit_mb: Maximum memory allowed in MB.
        time_limit_seconds: Maximum time allowed in seconds.

    Returns:
        A decorator that wraps the target function with monitoring logic.
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Start time monitoring
            time_enforcer = TimeLimitEnforcer(time_limit_seconds, f"Batch {func.__name__}")
            
            try:
                with time_enforcer:
                    # Initial memory check
                    enforce_memory_limit(memory_limit_mb)
                    
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Final checks after execution
                    enforce_memory_limit(memory_limit_mb)
                    time_enforcer.check()
                    
                    return result
            except (MemoryLimitExceededError, TimeLimitExceededError) as e:
                # Log the error or re-raise with context
                print(f"CRITICAL: {e}", file=sys.stderr)
                raise
        return wrapper
    return decorator


def main():
    """
    Standalone runner to demonstrate memory and time monitoring.
    This script can be run to verify the monitoring logic works before
    integrating it into the full diffusion pipeline.
    """
    import argparse
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(description="Monitor memory and time limits for generation.")
    parser.add_argument("--memory-limit", type=float, default=8192.0, help="Memory limit in MB")
    parser.add_argument("--time-limit", type=float, default=300.0, help="Time limit in seconds")
    parser.add_argument("--test-duration", type=float, default=1.0, help="Duration of test sleep to simulate work")
    
    args = parser.parse_args()

    logger.info(f"Starting monitor test with Memory Limit: {args.memory_limit} MB, Time Limit: {args.time_limit} s")

    try:
        with TimeLimitEnforcer(args.time_limit, "Test Operation"):
            logger.info(f"Current Memory: {get_memory_usage_mb():.2f} MB")
            enforce_memory_limit(args.memory_limit)
            
            # Simulate work
            logger.info(f"Simulating work for {args.test_duration}s...")
            time.sleep(args.test_duration)
            
            logger.info("Work completed successfully within limits.")
            enforce_memory_limit(args.memory_limit)

    except MemoryLimitExceededError as e:
        logger.error(f"Memory Limit Error: {e}")
        sys.exit(1)
    except TimeLimitExceededError as e:
        logger.error(f"Time Limit Error: {e}")
        sys.exit(1)

    logger.info("Monitor test passed.")

if __name__ == "__main__":
    main()
