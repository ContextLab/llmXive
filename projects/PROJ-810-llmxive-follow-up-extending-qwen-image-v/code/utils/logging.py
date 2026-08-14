"""
Structured logging and error tracking utilities for the llmXive pipeline.

This module provides:
- A centralized logger configuration that outputs JSON-formatted logs.
- Context managers for tracking execution duration and handling exceptions.
- Integration with project-specific result paths for error artifact generation.
"""

import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Callable, TypeVar

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_RESULTS_DIR = _PROJECT_ROOT / "data" / "results"

# Ensure results directory exists
_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Configuration constants
LOG_FILE_NAME = "pipeline.log"
ERROR_LOG_FILE_NAME = "errors.log"
LOG_FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Type variable for decorated functions
T = TypeVar("T", bound=Callable[..., Any])


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": "".join(
                    traceback.format_exception(*record.exc_info)
                ),
            }

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logger(
    name: str = "llmxive",
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True,
) -> logging.Logger:
    """
    Configure and return a structured logger.

    Args:
        name: Logger name.
        log_file: Path to log file. Defaults to PROJECT_ROOT/data/results/pipeline.log.
        level: Logging level.
        console: Whether to log to stdout.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    log_file_path = log_file or (_RESULTS_DIR / LOG_FILE_NAME)

    # File handler
    file_handler = logging.FileHandler(log_file_path, mode="a")
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(
            logging.Formatter(LOG_FORMATTER)
        )
        logger.addHandler(console_handler)

    return logger


def log_error_to_file(
    error: Exception,
    context: Dict[str, Any],
    task_id: Optional[str] = None,
) -> Path:
    """
    Log an exception to a dedicated error file with context.

    Args:
        error: The exception instance.
        context: Additional context data (e.g., task_id, inputs).
        task_id: Optional task identifier for filtering.

    Returns:
        Path to the error log file.
    """
    error_log_path = _RESULTS_DIR / ERROR_LOG_FILE_NAME

    error_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context,
    }

    if task_id:
        error_entry["task_id"] = task_id

    with open(error_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_entry) + "\n")

    return error_log_path


def get_logger(name: str = "llmxive") -> logging.Logger:
    """Retrieve an existing logger or create a default one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger


class ExecutionTimer:
    """Context manager to measure and log execution time."""

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        task_name: str = "Task",
    ):
        self.logger = logger or get_logger()
        self.task_name = task_name
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def __enter__(self) -> "ExecutionTimer":
        self.start_time = time.time()
        self.logger.info(f"Starting {self.task_name}")
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: Any,
    ) -> bool:
        self.end_time = time.time()
        duration = self.end_time - self.start_time

        if exc_type is None:
            self.logger.info(
                f"Completed {self.task_name} in {duration:.2f} seconds"
            )
        else:
            self.logger.error(
                f"Failed {self.task_name} after {duration:.2f} seconds: {exc_val}"
            )

        return False  # Do not suppress exceptions


def log_structured_event(
    event_type: str,
    data: Dict[str, Any],
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log a custom structured event.

    Args:
        event_type: Type of event (e.g., 'metric', 'checkpoint', 'error').
        data: Event payload.
        logger: Logger instance.
    """
    loggers = logger or get_logger()

    class ExtraDataLogRecord(logging.LogRecord):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.extra_data = data

    record = ExtraDataLogRecord(
        name=loggers.name,
        level=logging.INFO,
        fn="log_structured_event",
        lno=0,
        msg=f"Event: {event_type}",
        args=(),
        exc_info=None,
    )
    loggers.handle(record)


# Convenience functions for common logging patterns
def info(msg: str, logger: Optional[logging.Logger] = None) -> None:
    (logger or get_logger()).info(msg)

def error(
    msg: str,
    logger: Optional[logging.Logger] = None,
    exc_info: bool = True,
) -> None:
    (logger or get_logger()).error(msg, exc_info=exc_info)

def warning(msg: str, logger: Optional[logging.Logger] = None) -> None:
    (logger or get_logger()).warning(msg)

def debug(msg: str, logger: Optional[logging.Logger] = None) -> None:
    (logger or get_logger()).debug(msg)

def critical(msg: str, logger: Optional[logging.Logger] = None) -> None:
    (logger or get_logger()).critical(msg)