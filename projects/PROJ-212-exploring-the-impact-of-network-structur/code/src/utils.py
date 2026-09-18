"""
Utility functions for logging, error handling, and result checksumming.

This module provides centralized utilities used across the llmXive pipeline:
- setup_logging: Configure logging with file and console handlers.
- compute_checksum: Generate SHA-256 checksums for file integrity verification.
- log_error: Centralized error logging with stack trace capture.
- safe_exit: Graceful shutdown with status code handling.
- timing_decorator: Measure execution time of functions.
"""
import hashlib
import json
import logging
import sys
import os
import time
from pathlib import Path
from typing import Any, Dict, Union, Optional
from functools import wraps
import traceback


def setup_logging(
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Configure logging for the pipeline.
    
    Args:
        log_file: Optional path to a log file. If None, only console output is used.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console: If True, add a console handler.
        
    Returns:
        The root logger configured for this run.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def compute_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute a cryptographic checksum for a file.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default 'sha256').
        
    Returns:
        Hexadecimal string of the hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {path}")
    
    hasher = hashlib.new(algorithm)
    
    try:
        with open(path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
    except IOError as e:
        raise IOError(f"Failed to read file for checksum: {path}") from e
    
    return hasher.hexdigest()


def log_error(
    logger: logging.Logger,
    message: str,
    exception: Optional[Exception] = None,
    extra_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with optional exception traceback and context.
    
    Args:
        logger: The logger instance to use.
        message: The error message.
        exception: Optional exception instance to capture traceback.
        extra_context: Optional dictionary of additional context to log.
    """
    error_msg = message
    if extra_context:
        context_str = json.dumps(extra_context, default=str)
        error_msg = f"{message} | Context: {context_str}"
    
    if exception:
        logger.error(error_msg, exc_info=True)
    else:
        logger.error(error_msg)


def safe_exit(
    logger: Optional[logging.Logger] = None,
    status: int = 0,
    message: Optional[str] = None
) -> None:
    """
    Perform a safe exit, logging status if a logger is provided.
    
    Args:
        logger: Optional logger to record the exit status.
        status: Exit code (0 for success, non-zero for failure).
        message: Optional message to log before exiting.
    """
    if logger:
        if status == 0:
            logger.info(message or "Pipeline completed successfully.")
        else:
            logger.error(message or f"Pipeline exited with status code {status}.")
    
    sys.exit(status)


def timing_decorator(logger: Optional[logging.Logger] = None):
    """
    Decorator to measure and log the execution time of a function.
    
    Args:
        logger: Optional logger to record timing results.
        
    Returns:
        A wrapped function that logs its execution time.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                elapsed = end_time - start_time
                msg = f"{func.__name__} executed in {elapsed:.4f} seconds"
                if logger:
                    logger.info(msg)
                else:
                    print(msg)
        return wrapper
    return decorator
