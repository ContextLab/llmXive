"""
Logging infrastructure for the llmXive sensitivity analysis pipeline.

Provides structured JSON logging to `artifacts/run.log` and console output.
Ensures consistent formatting across all pipeline stages.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional

# Constants for log paths
ARTIFACTS_DIR = "artifacts"
LOG_FILE_PATH = os.path.join(ARTIFACTS_DIR, "run.log")
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Keep 5 backup files

# Global logger instance
_logger: Optional[logging.Logger] = None
_initialized: bool = False


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines.
    Includes timestamp, level, module, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)  # type: ignore[attr-defined]

        return json.dumps(log_data)


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves or creates a logger instance.

    Args:
        name: The name of the logger.

    Returns:
        A configured logger instance.
    """
    global _logger, _initialized

    if not _initialized:
        _setup_logging()
        _initialized = True

    return logging.getLogger(name)


def _setup_logging() -> None:
    """
    Configures the root logger with handlers for file (JSON) and console (text).
    Ensures the artifacts directory exists.
    """
    global _logger

    # Ensure artifacts directory exists
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    # File Handler (Rotating, JSON format)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to stderr if file logging fails
        sys.stderr.write(f"Warning: Could not initialize file logging: {e}\n")

    # Console Handler (Text format for readability)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Set the global logger reference
    _logger = root_logger


def log_event(
    event_type: str,
    message: str,
    level: int = logging.INFO,
    **kwargs: Any,
) -> None:
    """
    Logs a structured event with optional extra metadata.

    Args:
        event_type: A string categorizing the event (e.g., 'ingestion_start', 'resampling_complete').
        message: The primary log message.
        level: The logging level (e.g., logging.INFO, logging.ERROR).
        **kwargs: Additional key-value pairs to include in the JSON log entry.
    """
    logger = logging.getLogger("llmXive")
    
    # Create a log record with extra data
    extra = {"extra_data": {"event_type": event_type, **kwargs}}
    logger.log(level, message, extra=extra)


def log_error(
    message: str,
    exception: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Logs an error with optional exception details and context.

    Args:
        message: The error message.
        exception: The exception instance to format.
        context: Additional context dictionary.
    """
    logger = logging.getLogger("llmXive")
    extra = {}
    if context:
        extra["extra_data"] = {"context": context}
    
    if exception:
        logger.error(message, exc_info=exception, extra=extra)
    else:
        logger.error(message, extra=extra)
