import logging
import logging.handlers
import os
import sys
import json
import traceback
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from functools import wraps
from pathlib import Path

# Ensure the log directory exists
LOG_DIR = Path("outputs/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = LOG_DIR / "pipeline.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON for easy parsing."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        if hasattr(record, "context"):
            log_data["context"] = record.context

        return json.dumps(log_data)

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)
        level: Logging level

    Returns:
        Configured Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler for general logs
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    # Error file handler (only ERROR and above)
    error_handler = logging.FileHandler(ERROR_LOG_FILE)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)

    return logger

def handle_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    raise_error: bool = True,
) -> None:
    """
    Handle and log an error with context.

    Args:
        logger: Logger instance to use
        error: Exception that occurred
        context: Optional context dictionary to include in logs
        raise_error: Whether to re-raise the exception after logging
    """
    error_record = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
    }

    if context:
        error_record["context"] = context

    logger.error(
        f"Error occurred: {error}",
        extra={"context": context} if context else {},
        exc_info=True,
    )

    if raise_error:
        raise error

def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a message with additional context.

    Args:
        logger: Logger instance
        level: Logging level (e.g., logging.INFO)
        message: Log message
        context: Optional context dictionary
    """
    extra = {"context": context} if context else {}
    logger.log(level, message, extra=extra)

def time_execution(
    logger: Optional[logging.Logger] = None,
    level: int = logging.INFO,
) -> Callable:
    """
    Decorator to log the execution time of a function.

    Args:
        logger: Logger instance (creates default if None)
        level: Logging level for the timing message

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = get_logger(func.__module__)

            start_time = time.time()
            func_name = func.__name__

            log_with_context(
                logger,
                logging.DEBUG,
                f"Starting {func_name}",
                {"args": args, "kwargs": kwargs} if logger.isEnabledFor(logging.DEBUG) else None,
            )

            try:
                result = func(*args, **kwargs)
                elapsed_time = time.time() - start_time
                log_with_context(
                    logger,
                    level,
                    f"Completed {func_name} in {elapsed_time:.4f} seconds",
                    {"elapsed_seconds": elapsed_time},
                )
                return result
            except Exception as e:
                elapsed_time = time.time() - start_time
                handle_error(
                    logger,
                    e,
                    {
                        "function": func_name,
                        "elapsed_seconds": elapsed_time,
                        "args": args,
                        "kwargs": kwargs,
                    },
                )
                raise

        return wrapper
    return decorator

# Initialize a default logger for the pipeline module
logger = get_logger("pipeline")

# Convenience functions for quick logging
def info(msg: str, context: Optional[Dict] = None) -> None:
    log_with_context(logger, logging.INFO, msg, context)

def debug(msg: str, context: Optional[Dict] = None) -> None:
    log_with_context(logger, logging.DEBUG, msg, context)

def warning(msg: str, context: Optional[Dict] = None) -> None:
    log_with_context(logger, logging.WARNING, msg, context)

def error(msg: str, context: Optional[Dict] = None) -> None:
    log_with_context(logger, logging.ERROR, msg, context)

def critical(msg: str, context: Optional[Dict] = None) -> None:
    log_with_context(logger, logging.CRITICAL, msg, context)
