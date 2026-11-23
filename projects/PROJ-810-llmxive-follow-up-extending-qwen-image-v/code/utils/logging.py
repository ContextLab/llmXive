"""
Structured logging and error tracking utilities for the llmXive pipeline.

This module provides a JSON-formatted logging system that captures structured
events, errors, and execution metrics. It ensures all pipeline activities
are traceable and auditable.
"""

import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_handler: Optional[logging.Handler] = None


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON objects.
    Includes timestamp, level, message, and optional extra metadata.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add source location if available
        if record.pathname:
            log_data["file"] = os.path.basename(record.pathname)
            log_data["line"] = record.lineno

        # Add function name if available
        if record.funcName:
            log_data["function"] = record.funcName

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_data)


def setup_logger(
    log_dir: Union[str, Path],
    log_filename: str = "pipeline.log",
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Initialize and configure the global logger with JSON formatting.

    Args:
        log_dir: Directory to store log files.
        log_filename: Name of the log file.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console_output: Whether to also output to console.

    Returns:
        Configured logger instance.
    """
    global _logger, _log_handler

    if _logger is not None:
        return _logger

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    _logger = logging.getLogger("llmXive")
    _logger.setLevel(level)

    # Clear existing handlers
    _logger.handlers.clear()

    # File handler with JSON formatting
    log_file_path = log_path / log_filename
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setFormatter(JSONFormatter())
    _logger.addHandler(file_handler)
    _log_handler = file_handler

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        _logger.addHandler(console_handler)

    return _logger


def get_logger() -> logging.Logger:
    """
    Retrieve the global logger instance.

    Raises:
        RuntimeError: If logger has not been initialized.
    """
    if _logger is None:
        raise RuntimeError(
            "Logger not initialized. Call setup_logger() before using logging utilities."
        )
    return _logger


def log_structured_event(
    event_type: str,
    message: str,
    level: str = "INFO",
    **kwargs
) -> None:
    """
    Log a structured event with additional metadata.

    Args:
        event_type: Type of event (e.g., "START", "END", "ERROR", "METRIC").
        message: Human-readable message.
        level: Log level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        **kwargs: Additional metadata to include in the log entry.
    """
    logger = get_logger()

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    log_level = level_map.get(level.upper(), logging.INFO)

    extra = {"extra_data": {"event_type": event_type, **kwargs}}

    logger.log(log_level, message, extra=extra)


def log_error_to_file(
    error: Exception,
    context: str = "",
    log_dir: Optional[Union[str, Path]] = None
) -> Path:
    """
    Log an error with full traceback to a dedicated error log file.

    Args:
        error: The exception that occurred.
        context: Additional context about where the error occurred.
        log_dir: Directory to store error logs (uses default if not provided).

    Returns:
        Path to the error log file.
    """
    logger = get_logger()

    error_log_path = Path(log_dir) if log_dir else Path("data/results")
    error_log_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    error_filename = f"error_{timestamp}.log"
    error_file_path = error_log_path / error_filename

    error_content = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "traceback": traceback.format_exception(type(error), error, error.__traceback__),
    }

    with open(error_file_path, "w") as f:
        json.dump(error_content, f, indent=2)

    logger.error(f"Error logged to {error_file_path}", extra={"extra_data": {"error_type": type(error).__name__}})

    return error_file_path


class ExecutionTimer:
    """
    Context manager and utility for timing code execution blocks.
    Logs start/end times and duration as structured events.
    """

    def __init__(
        self,
        event_name: str,
        log_event: bool = True
    ):
        """
        Initialize the timer.

        Args:
            event_name: Name of the operation being timed.
            log_event: Whether to log the timing events.
        """
        self.event_name = event_name
        self.log_event = log_event
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None

    def __enter__(self) -> "ExecutionTimer":
        self.start_time = time.time()
        if self.log_event:
            log_structured_event(
                event_type="TIMER_START",
                message=f"Starting {self.event_name}",
                level="INFO",
                operation=self.event_name
            )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

        if self.log_event:
            log_structured_event(
                event_type="TIMER_END",
                message=f"Completed {self.event_name}",
                level="INFO",
                operation=self.event_name,
                duration_seconds=self.duration
            )

        if exc_type is not None:
            log_structured_event(
                event_type="TIMER_ERROR",
                message=f"Error during {self.event_name}",
                level="ERROR",
                operation=self.event_name,
                error_type=exc_type.__name__
            )

# Convenience functions for common log levels
def debug(msg: str, **kwargs) -> None:
    """Log a debug message."""
    log_structured_event("DEBUG", msg, level="DEBUG", **kwargs)

def info(msg: str, **kwargs) -> None:
    """Log an info message."""
    log_structured_event("INFO", msg, level="INFO", **kwargs)

def warning(msg: str, **kwargs) -> None:
    """Log a warning message."""
    log_structured_event("WARNING", msg, level="WARNING", **kwargs)

def error(msg: str, **kwargs) -> None:
    """Log an error message."""
    log_structured_event("ERROR", msg, level="ERROR", **kwargs)

def critical(msg: str, **kwargs) -> None:
    """Log a critical message."""
    log_structured_event("CRITICAL", msg, level="CRITICAL", **kwargs)


def main() -> None:
    """
    Demonstrate logging functionality with sample events.
    """
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        logger = setup_logger(tmpdir, console_output=True)

        info("Pipeline initialization started")

        with ExecutionTimer("sample_operation") as timer:
            time.sleep(0.1)
            info("Sample operation completed")

        try:
            raise ValueError("Test error for demonstration")
        except Exception as e:
            error_file = log_error_to_file(e, context="Main demonstration")
            info(f"Error logged to: {error_file}")

        log_structured_event(
            "METRIC_RECORD",
            "Sample metric recorded",
            level="INFO",
            metric_name="accuracy",
            metric_value=0.95
        )

        info("Pipeline demonstration completed")


if __name__ == "__main__":
    main()