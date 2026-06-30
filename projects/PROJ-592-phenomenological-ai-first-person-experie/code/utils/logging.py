"""
Logging utilities for the Phenomenological AI pipeline.

This module provides standardized logging configuration, logger retrieval,
warning capture mechanisms, and retry logic with exponential backoff.
All log output follows a consistent format to facilitate parsing and analysis.
"""

import logging
import sys
import time
import json
from functools import wraps
from typing import Callable, Any, Optional, List, Tuple
from pathlib import Path

# Standardized log levels mapping for clarity
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
}

# Default configuration
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Global warning capture storage
_captured_warnings: List[Tuple[str, str, int]] = []
_warning_handler: Optional[logging.Handler] = None


def _get_warning_handler() -> logging.Handler:
    """Create or retrieve the custom warning handler."""
    global _warning_handler
    if _warning_handler is None:
        _warning_handler = logging.Handler()
        _warning_handler.setLevel(logging.WARNING)
        _warning_handler.emit = lambda record: _capture_warning(record)
    return _warning_handler


def _capture_warning(record: logging.LogRecord) -> None:
    """Capture warning messages for later retrieval."""
    msg = record.getMessage()
    name = record.name
    level = record.levelname
    _captured_warnings.append((name, msg, level))


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    console_output: bool = True,
    json_mode: bool = False
) -> logging.Logger:
    """
    Configure the root logger with standardized settings.

    Args:
        log_level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to write logs to a file.
        console_output: Whether to output logs to stderr.
        json_mode: If True, output logs in JSON format.

    Returns:
        The root logger instance.
    """
    level = LOG_LEVELS.get(log_level.upper() if log_level else DEFAULT_LOG_LEVEL, logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Custom formatter based on mode
    if json_mode:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Add warning capture handler
    warning_handler = _get_warning_handler()
    if warning_handler not in root_logger.handlers:
        root_logger.addHandler(warning_handler)

    return root_logger


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'name': record.name,
            'levelname': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        if record.exc_info:
            log_data['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance with standardized configuration.

    Args:
        name: Logger name. If None, returns the root logger.

    Returns:
        Configured logger instance.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)


def capture_warning(logger: logging.Logger, message: str, *args, **kwargs) -> None:
    """
    Log a warning and ensure it is captured for retrieval.

    Args:
        logger: Logger instance to use.
        message: Warning message.
        *args: Arguments to format the message.
        **kwargs: Additional keyword arguments.
    """
    logger.warning(message, *args, **kwargs)


def get_captured_warnings() -> List[Tuple[str, str, str]]:
    """
    Retrieve all captured warning messages.

    Returns:
        List of tuples (logger_name, message, level).
    """
    return _captured_warnings.copy()


def clear_warnings() -> None:
    """Clear the captured warning log."""
    _captured_warnings.clear()


def export_warning_log(output_path: str) -> None:
    """
    Export captured warnings to a JSON file.

    Args:
        output_path: Path to write the warning log.
    """
    warnings = get_captured_warnings()
    data = [
        {'logger': name, 'message': msg, 'level': level}
        for name, msg, level in warnings
    ]
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def retry_on_failure(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[type, ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts.
        initial_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        backoff_factor: Multiplier for delay between attempts.
        exceptions: Tuple of exception types to catch.

    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break

                    logger = get_logger(func.__module__)
                    logger.warning(
                        "Attempt %d/%d failed for %s: %s. Retrying in %.2fs...",
                        attempt, max_attempts, func.__name__, str(e), delay
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            raise last_exception
        return wrapper
    return decorator


def log_retry_attempts(
    func: Callable,
    attempt: int,
    max_attempts: int,
    error: Exception,
    delay: float
) -> None:
    """
    Log a retry attempt for a function.

    Args:
        func: The function being retried.
        attempt: Current attempt number.
        max_attempts: Maximum allowed attempts.
        error: The exception that triggered the retry.
        delay: Delay before the next attempt.
    """
    logger = get_logger(func.__module__)
    logger.warning(
        "Retry attempt %d/%d for %s due to %s: %s. Waiting %.2fs.",
        attempt, max_attempts, func.__name__, type(error).__name__, str(error), delay
    )