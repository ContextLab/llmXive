"""
Logging configuration for the llmXive research pipeline.

Provides a JSON-formatted logging handler at INFO level to ensure
machine-readable logs for CI/CD pipelines and automated analysis.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.

    Includes timestamp, level, logger name, message, and optional
    extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure the root logger to output JSON-formatted logs to stdout.

    Args:
        level: The logging level to set (default: INFO).
    """
    # Prevent adding multiple handlers if called multiple times
    root_logger = logging.getLogger()
    if root_logger.handlers:
        # If handlers exist, assume they are already configured correctly
        # or return early to avoid duplication
        current_level = root_logger.level
        if current_level == level and any(
            isinstance(h, logging.StreamHandler) and h.stream == sys.stdout
            for h in root_logger.handlers
        ):
            return

    # Clear existing handlers to ensure a clean state
    root_logger.handlers.clear()

    # Create handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Set formatter
    formatter = JsonFormatter()
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger.setLevel(level)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger with the configured JSON formatting.

    Args:
        name: The name of the logger (typically __name__).

    Returns:
        A configured Logger instance.
    """
    logger = logging.getLogger(name)
    # Ensure the logger propagates to the root handler
    logger.propagate = True
    return logger


# Initialize logging immediately upon import to ensure consistency
# This ensures that any module importing this config gets the correct format
setup_logging()