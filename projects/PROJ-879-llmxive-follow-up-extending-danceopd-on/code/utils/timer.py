#!/usr/bin/env python
"""
Implement a cross-platform timeout mechanism for pipeline stages.
This module provides a unified timeout interface that works on both Unix (using SIGALRM)
and Windows (using threading), allowing pipeline stages to enforce hard time limits
and gracefully save partial results when exceeded.
"""
import signal
import time
import threading
import sys
from pathlib import Path
import json
import logging
from typing import Dict, Any, Optional, Callable

from utils.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom exception raised when a timeout occurs."""
    pass

# Global state for timeout management
_timeout_active = False
_timeout_thread: Optional[threading.Thread] = None
_start_time: Optional[float] = None
_timeout_duration: Optional[int] = None

def timeout_handler(signum, frame):
    """Signal handler for Unix SIGALRM timeout."""
    raise TimeoutError("Operation timed out")

def _windows_timer_func(duration: int):
    """Thread function for Windows timeout fallback."""
    time.sleep(duration)
    raise TimeoutError("Operation timed out")

def setup_timeout(seconds: int):
    """
    Set up a timeout mechanism.
    
    On Unix: Uses SIGALRM (signal-based).
    On Windows: Uses a daemon thread (threading-based).
    
    Args:
        seconds: Timeout duration in seconds.
    """
    global _timeout_active, _timeout_thread, _start_time, _timeout_duration
    
    _start_time = time.time()
    _timeout_duration = seconds
    _timeout_active = True

    if hasattr(signal, 'SIGALRM'):
        # Unix-like systems
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        logger.debug(f"Unix timeout set for {seconds} seconds via SIGALRM")
    else:
        # Windows fallback
        _timeout_thread = threading.Thread(target=_windows_timer_func, args=(seconds,), daemon=True)
        _timeout_thread.start()
        logger.debug(f"Windows timeout set for {seconds} seconds via threading")

def cancel_timeout():
    """Cancel any active timeout."""
    global _timeout_active
    
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)
    
    _timeout_active = False
    logger.debug("Timeout cancelled")

def check_timeout(timeout_seconds: int = 300) -> bool:
    """
    Check if the timeout has been exceeded.
    
    This function sets up a timeout and returns immediately.
    The actual timeout check happens when the calling code completes
    or when an exception is raised.
    
    For a blocking check, use with a try/except block:
        try:
            setup_timeout(timeout_seconds)
            # ... do work ...
        except TimeoutError:
            return False
        finally:
            cancel_timeout()
        return True
    
    Args:
        timeout_seconds: Timeout duration in seconds.
        
    Returns:
        True if timeout is active and hasn't expired yet.
        
    Raises:
        TimeoutError: If the timeout has been exceeded.
    """
    global _start_time, _timeout_duration
    
    if _timeout_active:
        # Check elapsed time if we're in a polling scenario
        if _start_time is not None and _timeout_duration is not None:
            elapsed = time.time() - _start_time
            if elapsed >= _timeout_duration:
                raise TimeoutError(f"Operation timed out after {elapsed:.2f} seconds")
    
    return True

def save_partial_results(config, results: Dict[str, Any], output_path: Optional[str] = None):
    """
    Save partial results to a JSON file when a timeout occurs.
    
    Args:
        config: Configuration object with get_path method.
        results: Dictionary of results to save.
        output_path: Optional custom path for the output file.
    """
    if output_path is None:
        results_dir = Path(config.get_path("RESULTS_DIR"))
        results_dir.mkdir(parents=True, exist_ok=True)
        partial_file = results_dir / "partial_results.json"
    else:
        partial_file = Path(output_path)
        partial_file.parent.mkdir(parents=True, exist_ok=True)

    # Ensure status is marked as partial
    results["status"] = "partial"
    results["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    results["timeout_seconds"] = _timeout_duration

    # Log remaining time if available
    if _start_time and _timeout_duration:
        elapsed = time.time() - _start_time
        results["elapsed_seconds"] = round(elapsed, 2)
        results["remaining_seconds"] = max(0, round(_timeout_duration - elapsed, 2))

    with open(partial_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Partial results saved to {partial_file}")
    return partial_file

def run_with_timeout(func: Callable, args: tuple = (), kwargs: dict = None, 
                    timeout_seconds: int = 300, 
                    on_timeout: Optional[Callable] = None) -> tuple:
    """
    Run a function with a timeout.
    
    Args:
        func: Function to execute.
        args: Positional arguments for func.
        kwargs: Keyword arguments for func.
        timeout_seconds: Timeout duration.
        on_timeout: Optional callback to run on timeout (receives partial results dict).
        
    Returns:
        Tuple of (success: bool, result: Any or None, partial_results_path: Optional[str])
    """
    if kwargs is None:
        kwargs = {}
        
    result = None
    partial_path = None
    success = False
    
    setup_timeout(timeout_seconds)
    try:
        result = func(*args, **kwargs)
        success = True
        return (True, result, None)
    except TimeoutError as e:
        logger.warning(f"Timeout exceeded: {e}")
        config = get_config()
        partial_results = {
            "error": str(e),
            "function": func.__name__,
            "args": args,
            "kwargs": kwargs
        }
        partial_path = save_partial_results(config, partial_results)
        
        if on_timeout:
            on_timeout(partial_results)
            
        return (False, None, str(partial_path))
    finally:
        cancel_timeout()

def main():
    """Command-line entry point for testing the timer module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Timer utility for pipeline stages")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    parser.add_argument("--test", action="store_true", help="Run a test timeout scenario")
    args = parser.parse_args()

    config = get_config()
    
    if args.test:
        logger.info("Running timeout test...")
        try:
            setup_timeout(args.timeout)
            time.sleep(min(args.timeout - 1, 5))  # Sleep for a bit but not past timeout
            logger.info("Test passed: No timeout occurred within test window")
        except TimeoutError:
            logger.warning("Test timeout triggered")
        finally:
            cancel_timeout()
    else:
        # Demonstrate the API
        logger.info(f"Timer module loaded. Use setup_timeout({args.timeout}) to start.")
        logger.info("Use check_timeout() to verify status.")
        logger.info("Use save_partial_results() to save state on timeout.")

if __name__ == "__main__":
    main()