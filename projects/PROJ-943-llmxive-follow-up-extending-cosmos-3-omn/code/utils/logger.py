"""
Logging infrastructure for llmXive.
Tracks memory usage and execution time.
"""
import logging
import os
import time
import tracemalloc
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

# Ensure logs directory exists
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "execution.log"

# Configure logger
logger = logging.getLogger("llmXive")
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler(LOG_FILE)
fh.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
fh.setFormatter(formatter)
ch.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(fh)
    logger.addHandler(ch)


def get_logger(name: str = "llmXive") -> logging.Logger:
    """Retrieve a logger instance."""
    return logging.getLogger(name)


def get_memory_usage_mb() -> float:
    """Get current memory usage in MB."""
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)


def log_memory_usage(msg: str = ""):
    """Log current memory usage."""
    mem = get_memory_usage_mb()
    if msg:
        logger.info(f"Memory Usage ({msg}): {mem:.2f} MB")
    else:
        logger.info(f"Current Memory Usage: {mem:.2f} MB")


@contextmanager
def track_execution_time(task_name: str = "Task"):
    """Context manager to track execution time of a block."""
    start_time = time.time()
    tracemalloc.start()
    log_memory_usage(f"Start of {task_name}")
    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(f"{task_name} completed in {duration:.2f} seconds. Peak memory: {peak / (1024 * 1024):.2f} MB")


def start_tracing():
    """Start tracing memory allocations."""
    tracemalloc.start()


def stop_tracing():
    """Stop tracing memory allocations."""
    if tracemalloc.is_tracing():
        tracemalloc.stop()


def log_script_start(script_path: str):
    """Log the start of a script execution."""
    logger.info(f"--- Script Start: {script_path} ---")
    start_tracing()


def log_script_end(script_path: str):
    """Log the end of a script execution."""
    stop_tracing()
    logger.info(f"--- Script End: {script_path} ---")