"""
Structured logging utility for the research pipeline.

Provides JSON-formatted logging for reproducibility and machine-readable logs.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Ensure the code directory is in the path for imports if running as script
if "code" not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class JsonFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs JSON lines.

    Each log record is serialized to a JSON object with:
    - timestamp: ISO 8601 formatted timestamp in UTC
    - level: Log level name
    - logger: Logger name
    - message: Log message
    - extra: Any additional fields from the log record
    """

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

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Handle exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Name for the logger (usually __name__).
        log_level: Optional log level override.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)

    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Default console level

    # Create file handler if LOG_FILE env var is set
    log_file = os.getenv("LOG_FILE")
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    # Set console formatter to JSON if JSON_LOGS env var is set, else standard
    if os.getenv("JSON_LOGS", "false").lower() == "true":
        console_handler.setFormatter(JsonFormatter())
    else:
        standard_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z"
        )
        console_handler.setFormatter(standard_formatter)

    logger.addHandler(console_handler)

    # Override level if provided
    if log_level:
        logger.setLevel(getattr(logging, log_level.upper()))

    return logger


def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    level: str = "INFO",
    **kwargs
) -> None:
    """
    Log a structured event with additional metadata.

    Args:
        logger: Logger instance to use.
        event_type: Type of event (e.g., "DATA_DOWNLOAD", "ANALYSIS_START").
        message: Human-readable message.
        level: Log level (DEBUG, INFO, WARNING, ERROR).
        **kwargs: Additional metadata to include in the log.
    """
    extra_data = {
        "event_type": event_type,
        **kwargs
    }

    # Create a new log record with extra data
    # We use a custom attribute 'extra_data' for the formatter
    record = logger.makeRecord(
        logger.name,
        getattr(logging, level.upper()),
        "",
        0,
        message,
        (),
        None
    )
    record.extra_data = extra_data

    logger.handle(record)


# Example usage and basic test
if __name__ == "__main__":
    test_logger = get_logger("test_logger")
    log_event(test_logger, "INIT", "Logger module initialized")
    log_event(test_logger, "TEST", "This is a test message with extra data", level="DEBUG", key1="value1")