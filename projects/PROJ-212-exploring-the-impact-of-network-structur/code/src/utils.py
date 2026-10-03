"""
Utility functions for logging, error handling, and result checksumming.

This module provides core infrastructure utilities used across the pipeline:
- setup_logging: Configure logging to file and console
- compute_checksum: Generate SHA-256 checksums for result files
- log_error: Standardized error logging
- safe_exit: Graceful shutdown with status code
- timing_decorator: Measure execution time of functions
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


def setup_logging(log_file: Optional[Union[str, Path]] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging to write to both file and console.

    Args:
        log_file: Path to the log file. If None, logs only to console.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        The root logger instance configured with the specified handlers.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def compute_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute the cryptographic checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hash_func = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e

    with open(file_path, 'rb') as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def log_error(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error with optional context information.

    Args:
        logger: The logger instance to use.
        error: The exception that occurred.
        context: Optional dictionary of contextual data (e.g., input parameters, state).
    """
    error_msg = f"Error: {type(error).__name__}: {str(error)}"
    if context:
        context_str = json.dumps(context, default=str)
        error_msg += f" | Context: {context_str}"
    logger.error(error_msg, exc_info=True)


def safe_exit(logger: Optional[logging.Logger] = None, status: int = 0, message: Optional[str] = None) -> None:
    """
    Perform a graceful exit, optionally logging a status message.

    Args:
        logger: Optional logger to record the exit.
        status: Exit code (0 for success, non-zero for failure).
        message: Optional message to log before exiting.
    """
    if logger:
        if status == 0:
            logger.info(message or "Pipeline completed successfully.")
        else:
            logger.error(message or f"Pipeline exited with status code {status}.")
    sys.exit(status)


def timing_decorator(func):
    """
    Decorator to measure and log the execution time of a function.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.time()
            elapsed = end_time - start_time
            # Log to the module logger if available, otherwise to root
            logger = logging.getLogger(func.__module__)
            if not logger.handlers:
                logger = logging.getLogger()
            logger.info(f"{func.__name__} completed in {elapsed:.4f} seconds")
    return wrapper
