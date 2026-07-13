"""
CPU-specific timing utilities for the llmXive pipeline.

Provides high-resolution wall-clock timing and context managers
for profiling CPU-bound operations using `time.perf_counter`.
Compatible with the project's logging and configuration infrastructure.
"""

import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
from pathlib import Path

# Local imports from project API surface
from utils.logger import get_logger
from config import is_ci_mode


_logger = get_logger(__name__)

# Global storage for timing results if needed across the session
_timing_results: Dict[str, float] = {}


def get_elapsed_time(start_time: float, end_time: Optional[float] = None) -> float:
    """
    Calculate the elapsed time in seconds between two timestamps.
    
    Args:
        start_time: Start timestamp from time.perf_counter()
        end_time: End timestamp. If None, uses current time.
        
    Returns:
        Elapsed time in seconds (float).
    """
    if end_time is None:
        end_time = time.perf_counter()
    return end_time - start_time


def profile_function(func):
    """
    Decorator to profile a function's execution time.
    
    Args:
        func: The function to profile.
        
    Returns:
        Wrapped function that logs execution time.
    """
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            func_name = func.__name__
            
            # Log based on mode
            if is_ci_mode():
                _logger.info(f"[CI] {func_name} executed in {elapsed:.4f}s")
            else:
                _logger.info(f"{func_name} executed in {elapsed:.4f}s")
            
            # Store result
            _timing_results[func_name] = elapsed
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            _logger.error(f"{func.__name__} failed after {elapsed:.4f}s: {e}")
            raise
    return wrapper


@contextmanager
def cpu_timer(label: str, log_level: str = "info"):
    """
    Context manager for timing a code block.
    
    Usage:
        with cpu_timer("my_operation"):
            # do work
            pass
    
    Args:
        label: Identifier for the timed section.
        log_level: Logging level ("info", "debug", "warning").
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        
        # Format log message
        msg = f"CPU Timer [{label}]: {elapsed:.4f}s"
        
        # Log based on mode and level
        if is_ci_mode():
            msg = f"[CI] " + msg
        
        if log_level == "debug":
            _logger.debug(msg)
        elif log_level == "warning":
            _logger.warning(msg)
        else:
            _logger.info(msg)
        
        # Store result
        _timing_results[label] = elapsed


def get_timing_report() -> Dict[str, float]:
    """
    Retrieve a report of all recorded timings.
    
    Returns:
        Dictionary mapping labels to elapsed times in seconds.
    """
    return _timing_results.copy()


def reset_timing_results():
    """Clear all stored timing results."""
    _timing_results.clear()
    _logger.debug("Timing results reset.")


def save_timing_results(output_path: str):
    """
    Save timing results to a JSON file.
    
    Args:
        output_path: Path to the output JSON file.
    """
    import json
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(_timing_results, f, indent=2)
    
    _logger.info(f"Timing results saved to {output_path}")