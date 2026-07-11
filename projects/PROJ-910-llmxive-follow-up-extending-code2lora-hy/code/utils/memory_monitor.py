"""
Memory monitoring utilities for the llmXive pipeline.

Implements FR-006 (2 cores, 7 GB RAM limit) and SC-004 (memory measurement).
Provides context managers and utility functions to enforce memory limits and log usage.
"""
import os
import csv
import resource
import time
import logging
import signal
from pathlib import Path
from typing import Optional, Callable, Any, Dict

# Constants
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024**3
RESULTS_DIR = Path("data/results")
MEMORY_LOG_PATH = RESULTS_DIR / "memory_log.csv"

# Configure logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def ensure_results_dir():
    """Ensure the results directory exists."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def get_current_memory_usage_bytes() -> float:
    """
    Get the current resident set size (RSS) memory usage in bytes.
    
    Returns:
        float: Current memory usage in bytes.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux/macOS
    return usage.ru_maxrss * 1024

def get_peak_memory_usage_bytes() -> float:
    """
    Get the peak resident set size (RSS) memory usage in bytes.
    
    Returns:
        float: Peak memory usage in bytes.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux/macOS
    return usage.ru_maxrss * 1024

def log_memory_usage(step_name: str, duration: Optional[float] = None):
    """
    Log current memory usage to the memory log CSV file.
    
    Args:
        step_name: Name of the current step/operation.
        duration: Optional duration of the step in seconds.
    """
    ensure_results_dir()
    
    current_mem = get_current_memory_usage_bytes()
    current_mem_gb = current_mem / (1024**3)
    peak_mem = get_peak_memory_usage_bytes()
    peak_mem_gb = peak_mem / (1024**3)
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    file_exists = MEMORY_LOG_PATH.exists()
    
    with open(MEMORY_LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'step_name', 'current_memory_gb', 'peak_memory_gb', 'duration_s'])
        
        writer.writerow([
            timestamp, 
            step_name, 
            f"{current_mem_gb:.4f}", 
            f"{peak_mem_gb:.4f}", 
            f"{duration:.4f}" if duration is not None else ""
        ])
    
    logger.info(f"Memory log: {step_name} - Current: {current_mem_gb:.2f} GB, Peak: {peak_mem_gb:.2f} GB")

def check_memory_limit() -> bool:
    """
    Check if current memory usage exceeds the 7 GB limit.
    
    Returns:
        bool: True if memory usage is within limits, False if it exceeds the limit.
    """
    current_mem = get_current_memory_usage_bytes()
    if current_mem > MEMORY_LIMIT_BYTES:
        current_mem_gb = current_mem / (1024**3)
        logger.error(f"Memory limit exceeded: {current_mem_gb:.2f} GB > {MEMORY_LIMIT_GB} GB")
        return False
    return True

def enforce_memory_limit():
    """
    Enforce the 7 GB memory limit by checking current usage.
    If exceeded, raises a MemoryError with a clear message.
    
    Raises:
        MemoryError: If memory usage exceeds 7 GB.
    """
    if not check_memory_limit():
        current_mem = get_current_memory_usage_bytes()
        current_mem_gb = current_mem / (1024**3)
        error_msg = (
            f"CRITICAL: Memory usage ({current_mem_gb:.2f} GB) exceeds the {MEMORY_LIMIT_GB} GB limit. "
            f"Aborting to prevent system instability (FR-006, FR-008)."
        )
        logger.error(error_msg)
        raise MemoryError(error_msg)

def memory_monitor_context(step_name: str):
    """
    Context manager to monitor memory usage for a specific step.
    Checks memory limit at entry and logs usage at exit.
    
    Args:
        step_name: Name of the step being monitored.
    
    Yields:
        None
    
    Raises:
        MemoryError: If memory usage exceeds the limit at entry.
    """
    # Check memory limit before entering the block
    enforce_memory_limit()
    
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        log_memory_usage(step_name, duration)
        # Final check after execution
        enforce_memory_limit()

def run_step_with_memory_logging(step_func: Callable, step_name: str, *args, **kwargs) -> Any:
    """
    Run a function with memory monitoring and logging.
    Checks memory limit before and after execution.
    
    Args:
        step_func: The function to execute.
        step_name: Name of the step for logging.
        *args: Positional arguments for step_func.
        **kwargs: Keyword arguments for step_func.
    
    Returns:
        Any: The return value of step_func.
    
    Raises:
        MemoryError: If memory usage exceeds the limit.
    """
    # Pre-check
    enforce_memory_limit()
    
    start_time = time.time()
    try:
        result = step_func(*args, **kwargs)
        return result
    finally:
        duration = time.time() - start_time
        log_memory_usage(step_name, duration)
        # Post-check
        enforce_memory_limit()

def main():
    """
    Main function to demonstrate memory monitoring functionality.
    Runs a simple test to verify logging and limit checking.
    """
    logger.info("Starting memory monitor demonstration...")
    
    # Ensure results directory
    ensure_results_dir()
    
    # Log initial state
    log_memory_usage("initialization", 0.0)
    
    # Simulate a step
    def dummy_step():
        time.sleep(0.1)
        return "completed"
    
    try:
        result = run_step_with_memory_logging(dummy_step, "dummy_step")
        logger.info(f"Step completed: {result}")
    except MemoryError as e:
        logger.error(f"Memory limit enforced: {e}")
    
    # Final check
    if check_memory_limit():
        logger.info("Memory check passed.")
    else:
        logger.error("Memory check failed.")

if __name__ == "__main__":
    main()