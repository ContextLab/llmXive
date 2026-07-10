"""
Structured JSON logging utility for the llmXive research pipeline.

Provides a centralized logger that outputs structured JSON logs suitable for
parsing by log aggregation systems. It also handles log levels and formatting
for both console and file outputs.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as a single line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the record
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger with JSON formatting.

    Args:
        name: The name of the logger (usually __name__).
        level: The logging level (e.g., logging.INFO).
        log_file: Optional path to a file to write logs to.
        console: If True, logs to stderr.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = JsonFormatter()

    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)

    return logger


def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    level: int = logging.INFO,
    **kwargs: Any,
) -> None:
    """
    Log a structured event with additional context.

    Args:
        logger: The logger instance to use.
        event_type: A short string identifying the type of event (e.g., 'data_ingest_start').
        message: The main log message.
        level: The severity level.
        **kwargs: Additional key-value pairs to include in the JSON log.
    """
    extra_data = {"event_type": event_type, **kwargs}
    record = logger.makeRecord(
        logger.name,
        level,
        "(unknown)",
        0,
        message,
        (),
        None,
        extra={"extra_data": extra_data},
    )
    logger.handle(record)
