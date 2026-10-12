"""
Utility functions for logging, error handling, and result checksumming.

This module provides centralized utilities used across the llmXive pipeline
to ensure consistent logging, robust error handling, and data integrity
verification via checksums.
"""
import hashlib
import json
import logging
import sys
import os
import time
from pathlib import Path
from typing import Any, Dict, Union, Optional, Callable
from functools import wraps

def setup_logging(
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Configure and return a logger with file and/or console handlers.

    Args:
        log_file: Path to the log file. If None, only console logging is configured.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console: If True, also log to stderr.

    Returns:
        A configured logger instance.
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
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def compute_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute the cryptographic checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal string of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


def log_error(
    logger: logging.Logger,
    message: str,
    exception: Optional[Exception] = None,
    extra_context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error message with optional exception traceback and context.

    Args:
        logger: The logger instance to use.
        message: The error message.
        exception: Optional exception instance to log traceback for.
        extra_context: Optional dictionary of extra context to log.
    """
    log_message = message
    if extra_context:
        context_str = json.dumps(extra_context, default=str)
        log_message = f"{message} | Context: {context_str}"

    if exception:
        logger.exception(log_message)
    else:
        logger.error(log_message)


def safe_exit(
    logger: logging.Logger,
    exit_code: int = 0,
    message: Optional[str] = None
) -> None:
    """
    Log an exit message and terminate the program safely.

    Args:
        logger: The logger instance to use.
        exit_code: The exit code (0 for success, non-zero for failure).
        message: Optional message to log before exiting.
    """
    if message:
        if exit_code == 0:
            logger.info(message)
        else:
            logger.error(message)
    sys.exit(exit_code)


def timing_decorator(logger: Optional[logging.Logger] = None) -> Callable:
    """
    Decorator to log the execution time of a function.

    Args:
        logger: Optional logger instance. If None, prints to console.

    Returns:
        A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                duration = end_time - start_time
                msg = f"Function '{func.__name__}' completed in {duration:.4f} seconds"
                if logger:
                    logger.info(msg)
                else:
                    print(msg)
        return wrapper
    return decorator

# ----------------------------------------------------------------------
# Additional utilities required by task T007
# ----------------------------------------------------------------------

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Wrapper around the platform‑wide ``llmxive_toolkit.get_logger``.

    This function mirrors the project's existing convention of obtaining a
    logger via ``get_logger(__name__)`` while keeping the implementation
    local to this module for ease of import.

    Args:
        name: The name to associate with the logger (defaults to the caller's module).

    Returns:
        A configured ``logging.Logger`` instance.
    """
    from llmxive_toolkit import get_logger as toolkit_get_logger
    return toolkit_get_logger(name)


def save_json(
    obj: Any,
    path: Union[str, Path],
    schema_path: Optional[Union[str, Path]] = None
) -> None:
    """
    Serialize *obj* to JSON, write it to *path* with an indent of 2 spaces,
    and optionally validate the object against a JSON schema.

    The function raises ``jsonschema.ValidationError`` if validation fails,
    propagating the exception so that callers (including the test suite) can
    detect the problem.

    Args:
        obj: Any JSON‑serialisable Python object.
        path: Destination file path (string or ``Path``). Parent directories are created automatically.
        schema_path: Optional path to a JSON schema (YAML or JSON). If provided,
                     the object is validated against this schema before writing.

    Returns:
        None
    """
    import json
    import yaml
    import jsonschema

    # Ensure we have a Path object and that its parent directory exists.
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # If a schema is supplied, load it (YAML is common in this repo) and validate.
    if schema_path is not None:
        schema_file = Path(schema_path)
        with schema_file.open('r') as sf:
            # ``yaml.safe_load`` works for both YAML and JSON content.
            schema = yaml.safe_load(sf)
        jsonschema.validate(instance=obj, schema=schema)

    # Write the JSON file with the required pretty‑print formatting.
    with out_path.open('w', encoding='utf-8') as fp:
        json.dump(obj, fp, indent=2, ensure_ascii=False)
