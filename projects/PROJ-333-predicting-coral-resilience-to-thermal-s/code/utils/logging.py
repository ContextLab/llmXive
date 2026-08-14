import os
import sys
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with console and optional file handlers.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_memory_usage_mb() -> float:
    """
    Gets current memory usage in MB.
    
    Returns:
        Memory usage in MB
    """
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0  # Convert KB to MB on Linux

def log_memory_usage(logger: logging.Logger, message: str = "Current memory usage") -> None:
    """Logs current memory usage."""
    mem = get_memory_usage_mb()
    logger.info(f"{message}: {mem:.2f} MB")

class MemoryTracker:
    """Context manager to track memory usage changes."""
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_mem = 0.0

    def __enter__(self):
        self.start_mem = get_memory_usage_mb()
        self.logger.info(f"Starting {self.operation} at {self.start_mem:.2f} MB")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_mem = get_memory_usage_mb()
        delta = end_mem - self.start_mem
        self.logger.info(f"Finished {self.operation}. Memory delta: {delta:.2f} MB (Peak: {end_mem:.2f} MB)")

class ExecutionTimer:
    """Context manager to time code execution."""
    def __init__(self, logger: logging.Logger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time = 0.0

    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        self.logger.info(f"Finished {self.operation} in {elapsed:.2f} seconds")

def log_execution_time(logger: logging.Logger, operation: str, func, *args, **kwargs):
    """Decorator-like function to log execution time of a function."""
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    logger.info(f"{operation} completed in {end - start:.2f} seconds")
    return result
