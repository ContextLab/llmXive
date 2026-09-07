"""
Utility functions for logging, error handling, and result checksumming.

This module provides centralized utilities to ensure consistent logging
configuration, robust error handling with detailed context, and data integrity
verification via checksums.
"""
import hashlib
import json
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, Union, Optional, Callable
from functools import wraps
import time


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    module_name: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with standardized formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, logs only to stdout.
        module_name: Optional name for the logger. Defaults to the calling module.
    
    Returns:
        Configured logger instance.
    """
    # Determine logger name
    if module_name is None:
        frame = sys._getframe(1)
        module_name = frame.f_globals.get("__name__", "root")
    
    logger = logging.getLogger(module_name)
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def compute_checksum(data: Union[str, bytes, Dict, Any], algorithm: str = "sha256") -> str:
    """
    Compute a cryptographic checksum of the provided data.
    
    Supports strings, bytes, dictionaries, and other serializable objects.
    Dictionaries are sorted by key before hashing to ensure deterministic output.
    
    Args:
        data: The data to hash.
        algorithm: Hash algorithm to use (default: sha256).
    
    Returns:
        Hexadecimal string of the hash digest.
    
    Raises:
        ValueError: If the algorithm is not supported.
    """
    hasher = hashlib.new(algorithm)
    
    if isinstance(data, str):
        hasher.update(data.encode("utf-8"))
    elif isinstance(data, bytes):
        hasher.update(data)
    elif isinstance(data, dict):
        # Serialize dict with sorted keys to ensure determinism
        serialized = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        hasher.update(serialized)
    else:
        # Fallback: try to serialize as JSON
        try:
            serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
            hasher.update(serialized)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Cannot serialize data for checksum: {e}")
    
    return hasher.hexdigest()


def log_error(
    logger: logging.Logger,
    message: str,
    error: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None,
    level: str = "ERROR"
) -> None:
    """
    Log an error message with optional exception details and context.
    
    Args:
        logger: The logger instance to use.
        message: The error message.
        error: Optional exception instance to log traceback details.
        context: Optional dictionary of additional context variables.
        level: Log level string (default: ERROR).
    """
    log_method = getattr(logger, level.lower(), logger.error)
    
    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        full_message = f"{message} | Context: {context_str}"
    else:
        full_message = message
    
    if error:
        log_method(f"{full_message} | Exception: {type(error).__name__}: {str(error)}")
        # Log traceback at debug level for deeper inspection
        logger.debug("Traceback details:", exc_info=error)
    else:
        log_method(full_message)


def safe_exit(
    logger: logging.Logger,
    exit_code: int = 0,
    message: Optional[str] = None,
    error: Optional[Exception] = None
) -> None:
    """
    Log a final status message and exit the program.
    
    Args:
        logger: The logger instance to use.
        exit_code: Exit code (0 for success, non-zero for failure).
        message: Optional final status message.
        error: Optional exception if exiting due to error.
    """
    if exit_code == 0:
        if message:
            logger.info(f"SUCCESS: {message}")
        else:
            logger.info("Process completed successfully.")
    else:
        if message:
            log_error(logger, message, error=error, level="CRITICAL")
        else:
            log_error(logger, "Process terminated with error.", error=error, level="CRITICAL")
    
    sys.exit(exit_code)


def timing_decorator(logger: Optional[logging.Logger] = None, log_level: str = "INFO"):
    """
    Decorator to log the execution time of a function.
    
    Args:
        logger: Logger instance. If None, creates a temporary one.
        log_level: Log level for timing messages.
    
    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = setup_logging(module_name=func.__module__)
            
            log_method = getattr(logger, log_level.lower(), logger.info)
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                log_method(f"Function '{func.__name__}' completed in {elapsed:.4f} seconds.")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                log_error(
                    logger, 
                    f"Function '{func.__name__}' failed after {elapsed:.4f} seconds.", 
                    error=e
                )
                raise
        return wrapper
    return decorator
