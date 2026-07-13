"""
Logging configuration for the llmXive statistical analysis pipeline.

This module sets up a centralized logging infrastructure that:
1. Configures a hierarchical logger hierarchy under 'llmXive'.
2. Handles log levels based on environment variables or configuration.
3. Implements structured JSON logging for machine-parseable logs (optional).
4. Provides a consistent error handling wrapper for exceptions.
5. Ensures logs are written to both console and file (under state/logs/).
"""

import logging
import logging.handlers
import os
import sys
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from functools import wraps

# Attempt to import optional dependencies for structured logging
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from src.config import get_config

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
LOG_DIR = Path("state/logs")
LOG_FILE_NAME = "pipeline.log"
JSON_LOG_FILE_NAME = "pipeline.json"
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5
LOGGER_NAME = "llmXive"


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        if hasattr(record, 'extra_data'):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves a logger configured with the project's standards.

    Args:
        name: Optional sub-logger name. If None, returns the root 'llmXive' logger.

    Returns:
        A configured logging.Logger instance.
    """
    root_logger = logging.getLogger(LOGGER_NAME)

    if not root_logger.handlers:
        _setup_logging()

    if name:
        return root_logger.getChild(name)
    return root_logger


def _setup_logging() -> None:
    """
    Configures the root logger with console and file handlers.
    Reads configuration from src.config if available, otherwise uses defaults.
    """
    root_logger = logging.getLogger(LOGGER_NAME)
    root_logger.setLevel(DEFAULT_LOG_LEVEL)

    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Determine log level from config or environment
    config = get_config()
    level_name = os.getenv("LLMXIVE_LOG_LEVEL", "INFO")
    if hasattr(config, "log_level"):
        level_name = getattr(config, "log_level", level_name)

    try:
        level = getattr(logging, level_name.upper(), logging.INFO)
    except AttributeError:
        level = logging.INFO

    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (Rotating)
    file_path = LOG_DIR / LOG_FILE_NAME
    file_handler = logging.handlers.RotatingFileHandler(
        file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(console_formatter)
    root_logger.addHandler(file_handler)

    # Optional JSON File Handler for machine parsing
    json_file_path = LOG_DIR / JSON_LOG_FILE_NAME
    json_handler = logging.handlers.RotatingFileHandler(
        json_file_path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8"
    )
    json_handler.setLevel(logging.DEBUG) # Capture debug in JSON if needed
    json_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(json_handler)


def handle_error(logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Centralized error handling wrapper.

    Logs the error with full traceback and optional context data,
    then re-raises the exception.

    Args:
        logger: The logger instance to use.
        error: The exception instance.
        context: Optional dictionary of contextual data to attach to the log.
    """
    log_record = logger.makeRecord(
        logger.name,
        logging.ERROR,
        "",
        0,
        str(error),
        (),
        error
    )

    if context:
        log_record.extra_data = context

    logger.handle(log_record)
    raise error


def log_with_context(logger: logging.Logger, level: int, message: str, **kwargs) -> None:
    """
    Logs a message with additional structured context data.

    Args:
        logger: The logger instance.
        level: The logging level (e.g., logging.INFO).
        message: The log message.
        **kwargs: Additional key-value pairs to include in the log entry.
    """
    class ContextAdapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            return msg, kwargs

    # We attach extra_data directly to the record if possible,
    # but standard LoggerAdapter doesn't support arbitrary fields easily.
    # Instead, we format the message or use a custom method if needed.
    # For simplicity in this config, we append context to the message string
    # or rely on the JSONFormatter to pick up 'extra' if we set it.

    # Simpler approach: Append context to message for text logs,
    # and use a custom log method for JSON.
    if kwargs:
        context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        full_message = f"{message} [{context_str}]"
    else:
        full_message = message

    logger.log(level, full_message)


def time_execution(logger: logging.Logger, task_name: str) -> Callable:
    """
    Decorator to log the execution time of a function.

    Args:
        logger: The logger instance.
        task_name: Name of the task for logging.

    Returns:
        A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = datetime.now()
            logger.info(f"Starting task: {task_name}")
            try:
                result = func(*args, **kwargs)
                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Completed task: {task_name} in {duration:.2f}s")
                return result
            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(f"Failed task: {task_name} after {duration:.2f}s", exc_info=True)
                raise
        return wrapper
    return decorator

# Initialize logger immediately on import to ensure setup runs
# This is safe because _setup_logging checks for existing handlers.
_logger = get_logger()
_logger.debug("Logging infrastructure initialized.")
