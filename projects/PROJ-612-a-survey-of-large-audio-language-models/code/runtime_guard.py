"""
Runtime time-limit guard and OOM handling logic for the LALM survey pipeline.

This module provides:
1. A context manager and decorator to enforce a configurable CPU time limit.
2. A decorator to catch OOM errors (simulated or real) and trigger graceful aborts.
3. Logging integration with the existing project logging infrastructure.
"""

import os
import signal
import sys
import resource
import logging
import time
from functools import wraps
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Import existing logging infrastructure
try:
    from setup_logging import get_logger, log_error
except ImportError:
    # Fallback if run in isolation, though project structure should allow import
    logging.basicConfig(level=logging.INFO)
    def get_logger(name): return logging.getLogger(name)
    def log_error(msg, exc=None): logging.error(msg, exc_info=exc)

# Import existing config utilities
try:
    from config import load_config
except ImportError:
    # Fallback if config.py is not found or import fails
    def load_config(path: Optional[str] = None) -> dict:
        # Default fallback config if file missing
        return {
            "runtime": {
                "time_limit_seconds": 3600,
                "oom_memory_limit_mb": 6000
            }
        }

logger = get_logger("runtime_guard")

# Global flag to track if we are in an aborted state
_aborted = False
_abort_reason = ""

def _handle_timeout(signum, frame):
    """Signal handler for time limit expiration."""
    global _aborted, _abort_reason
    _aborted = True
    _abort_reason = "TIME_LIMIT_EXCEEDED"
    logger.critical(f"Runtime guard: Execution time limit exceeded. Terminating gracefully.")
    # Raise an exception to break out of the current execution flow immediately
    raise TimeoutError("TIME_LIMIT_EXCEEDED")

def _handle_oom(signum, frame):
    """Signal handler for memory limit (SIGXCPU or simulated OOM)."""
    global _aborted, _abort_reason
    _aborted = True
    _abort_reason = "OOM_EXCEEDED"
    logger.critical(f"Runtime guard: Out of Memory limit exceeded. Terminating gracefully.")
    raise MemoryError("OOM_EXCEEDED")

def get_runtime_config() -> dict:
    """Load runtime configuration from config.yaml or defaults."""
    try:
        cfg = load_config()
        return cfg.get("runtime", {
            "time_limit_seconds": 3600,
            "oom_memory_limit_mb": 6000
        })
    except Exception as e:
        logger.warning(f"Failed to load runtime config: {e}. Using defaults.")
        return {
            "time_limit_seconds": 3600,
            "oom_memory_limit_mb": 6000
        }

@contextmanager
def time_limit_guard(seconds: Optional[int] = None):
    """
    Context manager to enforce a CPU time limit.
    
    Args:
        seconds: Time limit in seconds. If None, reads from config.
    
    Yields:
        None
    
    Raises:
        TimeoutError: If the time limit is exceeded.
    """
    if seconds is None:
        config = get_runtime_config()
        seconds = config.get("time_limit_seconds", 3600)
    
    if seconds <= 0:
        logger.warning("Time limit is <= 0, skipping time guard.")
        yield
        return

    logger.info(f"Setting CPU time limit to {seconds} seconds.")
    
    # Save old handler
    old_handler = signal.signal(signal.SIGALRM, _handle_timeout)
    # Set the alarm
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Cancel the alarm
        signal.alarm(0)
        # Restore old handler
        signal.signal(signal.SIGALRM, old_handler)

@contextmanager
def memory_limit_guard(mb_limit: Optional[int] = None):
    """
    Context manager to enforce a soft memory limit using resource limits.
    
    Note: This sets the RLIMIT_AS (virtual memory) or RLIMIT_DATA.
    On some systems, this may kill the process immediately if exceeded.
    We catch the signal and raise a controlled exception.
    
    Args:
        mb_limit: Memory limit in MB. If None, reads from config.
    
    Yields:
        None
    
    Raises:
        MemoryError: If the memory limit is exceeded.
    """
    if mb_limit is None:
        config = get_runtime_config()
        mb_limit = config.get("oom_memory_limit_mb", 6000)
    
    if mb_limit <= 0:
        logger.warning("Memory limit is <= 0, skipping memory guard.")
        yield
        return

    # Convert MB to bytes
    limit_bytes = mb_limit * 1024 * 1024
    
    # Get current limits
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    
    logger.info(f"Setting memory limit to {mb_limit} MB ({limit_bytes} bytes).")
    
    # Set new limits (soft limit triggers the signal, hard kills)
    # We set both to the limit to ensure enforcement
    try:
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
    except ValueError as e:
        logger.warning(f"Could not set RLIMIT_AS: {e}. Memory guard may be ineffective on this platform.")
        yield
        return

    # Set up signal handler for SIGXCPU (though RLIMIT_AS usually kills, 
    # some systems might use SIGXCPU for soft limits depending on config)
    # Note: RLIMIT_AS violation usually results in SIGKILL which cannot be caught.
    # However, we can try to catch SIGXCPU if the system uses it for soft limits.
    old_handler = signal.signal(signal.SIGXCPU, _handle_oom)
    
    try:
        yield
    except MemoryError:
        # Re-raise if we caught it from our own logic
        raise
    finally:
        # Restore limits to previous state if possible (best effort)
        try:
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
        except ValueError:
            pass
        signal.signal(signal.SIGXCPU, old_handler)

def with_runtime_guards(time_limit: Optional[int] = None, memory_limit: Optional[int] = None):
    """
    Decorator to wrap a function with time and memory limits.
    
    Args:
        time_limit: Seconds.
        memory_limit: MB.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                with time_limit_guard(time_limit):
                    with memory_limit_guard(memory_limit):
                        return func(*args, **kwargs)
            except (TimeoutError, MemoryError) as e:
                log_error(f"Function {func.__name__} aborted due to guard: {e}")
                # Re-raise to allow the caller to handle the abort
                raise
        return wrapper
    return decorator

def check_aborted() -> bool:
    """Check if a global abort flag has been set."""
    return _aborted

def get_abort_reason() -> str:
    """Get the reason for the last abort."""
    return _abort_reason

def main():
    """
    CLI entry point to test the guards.
    Usage: python code/runtime_guard.py --time 5 --memory 100
    """
    import argparse
    parser = argparse.ArgumentParser(description="Test runtime guards")
    parser.add_argument("--time", type=int, default=None, help="Time limit in seconds")
    parser.add_argument("--memory", type=int, default=None, help="Memory limit in MB")
    args = parser.parse_args()

    logger.info("Starting runtime guard test.")

    @with_runtime_guards(time_limit=args.time, memory_limit=args.memory)
    def heavy_task():
        logger.info("Simulating heavy task...")
        # Simulate work
        for i in range(100000000):
            if i % 10000000 == 0:
                logger.info(f"Working... {i}")
            _ = i * i
        logger.info("Task completed successfully.")
        return "Done"

    try:
        result = heavy_task()
        print(f"Result: {result}")
    except (TimeoutError, MemoryError) as e:
        print(f"Guard triggered: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
