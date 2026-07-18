"""
Structured logging and error tracking utilities for the elastic anisotropy pipeline.

This module provides a consistent logging interface with JSON formatting for
machine-readable logs and standard logging for human-readable output.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Any, Dict
import traceback


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add location info if available
        if hasattr(record, "filename"):
            log_data["location"] = {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields if present
        if hasattr(record, "__dict__"):
            extra_fields = {
                k: v for k, v in record.__dict__.items()
                if k not in {"msg", "args", "levelname", "levelno", "pathname",
                             "filename", "module", "lineno", "funcName",
                             "created", "msecs", "relativeCreated", "thread",
                             "threadName", "processName", "process", "exc_info",
                             "exc_text", "stack_info", "message", "name", "pathname"}
            }
            if extra_fields:
                log_data["extra"] = extra_fields

        return json.dumps(log_data)


def setup_logger(
    name: str = "elastic_anisotropy",
    level: int = logging.INFO,
    json_output: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with consistent formatting and handlers.

    Args:
        name: Logger name (usually module name)
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        json_output: If True, use JSON formatter; otherwise use standard format
        log_file: Optional path to write logs to a file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Clear any existing handlers from parent loggers to prevent duplication
    logger.propagate = False

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_output:
        console_handler.setFormatter(JsonFormatter())
    else:
        # Standard format for human readability
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        if json_output:
            file_handler.setFormatter(JsonFormatter())
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Global logger instance (lazy initialization)
_logger: Optional[logging.Logger] = None


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance.

    Args:
        name: Optional logger name. If None, returns the default logger.

    Returns:
        Logger instance
    """
    global _logger

    if name is None:
        if _logger is None:
            _logger = setup_logger()
        return _logger

    return setup_logger(name)


def log_info(message: str, logger_name: Optional[str] = None, **kwargs: Any) -> None:
    """Log an informational message."""
    logger = get_logger(logger_name)
    logger.info(message, extra=kwargs)


def log_warning(message: str, logger_name: Optional[str] = None, **kwargs: Any) -> None:
    """Log a warning message."""
    logger = get_logger(logger_name)
    logger.warning(message, extra=kwargs)


def log_error(message: str, logger_name: Optional[str] = None, **kwargs: Any) -> None:
    """Log an error message."""
    logger = get_logger(logger_name)
    logger.error(message, extra=kwargs)


def log_debug(message: str, logger_name: Optional[str] = None, **kwargs: Any) -> None:
    """Log a debug message."""
    logger = get_logger(logger_name)
    logger.debug(message, extra=kwargs)


def log_success(message: str, logger_name: Optional[str] = None, **kwargs: Any) -> None:
    """Log a success message (using INFO level with custom formatting)."""
    logger = get_logger(logger_name)
    # Use a custom level or just info with context
    logger.info(f"SUCCESS: {message}", extra=kwargs)


# Convenience function to configure logging for the entire pipeline
def configure_pipeline_logging(
    log_file: Optional[str] = None,
    json_format: bool = False,
    level: int = logging.INFO
) -> None:
    """
    Configure logging for the entire pipeline.

    Args:
        log_file: Optional path to write logs to a file
        json_format: If True, use JSON formatting
        level: Logging level for the pipeline
    """
    global _logger
    _logger = setup_logger(
        name="elastic_anisotropy_pipeline",
        level=level,
        json_output=json_format,
        log_file=log_file
    )