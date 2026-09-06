"""
Structured logging utility for the llmXive research pipeline.

Provides a centralized logger configuration that outputs structured logs
(JSON format) to stdout and stderr, with support for log levels,
correlation IDs, and consistent formatting across the project.

Usage:
    from utils.logging import get_logger, configure_logging

    logger = get_logger(__name__)
    logger.info("Starting analysis", extra={"step": "init"})
"""

import logging
import sys
import json
import os
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from logging import Logger, Filter
import traceback

# Default configuration
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMATTER_TYPE = "json"  # Options: 'json', 'text'
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

# Global logger registry
_loggers: Dict[str, Logger] = {}
_configured = False


class StructuredJsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON objects.
    Includes timestamp, level, logger name, message, and extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": "".join(
                    traceback.format_exception(*record.exc_info)
                )
                if record.exc_info
                else None,
            }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id

        return json.dumps(log_entry)


class TextFormatter(logging.Formatter):
    """
    Standard text formatter with ISO timestamp and context.
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)
        return (
            f"{timestamp} [{record.levelname:8}] {record.name}: "
            f"{record.getMessage()}"
        )


class CorrelationIdFilter(Filter):
    """
    Filter to inject correlation ID from context into log records.
    """

    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id or os.getenv(
            "LLMXIVE_CORRELATION_ID", "default"
        )

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "correlation_id"):
            record.correlation_id = self.correlation_id
        return True


def get_logger(
    name: str,
    level: Union[str, int] = DEFAULT_LOG_LEVEL,
    correlation_id: Optional[str] = None,
) -> Logger:
    """
    Get or create a logger with the specified name.

    Args:
        name: Logger name (usually __name__)
        level: Log level (string or int)
        correlation_id: Optional correlation ID for request tracing

    Returns:
        Configured Logger instance
    """
    global _configured

    if name in _loggers:
        return _loggers[name]

    # Ensure logging is configured
    if not _configured:
        configure_logging()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Add correlation filter if provided
    if correlation_id:
        logger.addFilter(CorrelationIdFilter(correlation_id))

    # Avoid adding handlers multiple times if get_logger is called repeatedly
    # before configure_logging completes
    if not logger.handlers:
        # Handlers are added in configure_logging, but ensure we don't duplicate
        # if this is called after configure_logging
        pass

    _loggers[name] = logger
    return logger


def configure_logging(
    log_level: Union[str, int] = DEFAULT_LOG_LEVEL,
    formatter_type: str = LOG_FORMATTER_TYPE,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Configure the root logger with structured output.

    Args:
        log_level: Minimum log level to display
        formatter_type: 'json' or 'text'
        correlation_id: Global correlation ID if not using environment variable
    """
    global _configured

    if _configured:
        return

    # Set root logger level
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatters
    if formatter_type == "json":
        formatter = StructuredJsonFormatter()
    else:
        formatter = TextFormatter()

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Create stderr handler for errors and above
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)

    # Add correlation filter
    if correlation_id:
        console_handler.addFilter(CorrelationIdFilter(correlation_id))
        stderr_handler.addFilter(CorrelationIdFilter(correlation_id))

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(stderr_handler)

    _configured = True


def set_correlation_id(correlation_id: str) -> None:
    """
    Set a global correlation ID for the current process.

    Args:
        correlation_id: Unique identifier for request tracing
    """
    os.environ["LLMXIVE_CORRELATION_ID"] = correlation_id


def log_with_context(
    logger: Logger,
    level: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> None:
    """
    Log a message with additional context fields.

    Args:
        logger: Logger instance
        level: Log level ('debug', 'info', 'warning', 'error', 'critical')
        message: Log message
        context: Dictionary of additional fields to include
        **kwargs: Additional keyword arguments passed to log method
    """
    extra = {"extra_data": context or {}} if context else {}
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=extra, **kwargs)


# Convenience functions for quick logging without explicit logger
def info(msg: str, **kwargs) -> None:
    """Log info message to default logger."""
    logger = get_logger("root")
    log_with_context(logger, "info", msg, **kwargs)


def warning(msg: str, **kwargs) -> None:
    """Log warning message to default logger."""
    logger = get_logger("root")
    log_with_context(logger, "warning", msg, **kwargs)


def error(msg: str, **kwargs) -> None:
    """Log error message to default logger."""
    logger = get_logger("root")
    log_with_context(logger, "error", msg, **kwargs)


def debug(msg: str, **kwargs) -> None:
    """Log debug message to default logger."""
    logger = get_logger("root")
    log_with_context(logger, "debug", msg, **kwargs)


def critical(msg: str, **kwargs) -> None:
    """Log critical message to default logger."""
    logger = get_logger("root")
    log_with_context(logger, "critical", msg, **kwargs)

if __name__ == "__main__":
    # Example usage
    configure_logging(log_level="DEBUG", formatter_type="json")
    logger = get_logger(__name__)

    logger.info("Starting structured logging demo")
    logger.warning("This is a warning with context", context={"key": "value"})
    logger.error("This is an error", context={"error_code": 500})

    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("Caught an exception")

    logger.info("Demo complete")