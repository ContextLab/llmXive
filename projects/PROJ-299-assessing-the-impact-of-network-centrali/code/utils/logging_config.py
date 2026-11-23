"""
Logging Configuration Module

Provides machine-readable (JSON) logging infrastructure for the pipeline.
Writes logs to `logs/pipeline.log` as per FR-011.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from code.config.env_config import get_config


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Ensures machine-readable logs for automated analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra data if present
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        return json.dumps(log_data)


def setup_logging(
    log_path: Union[str, Path],
    level: str = "INFO",
    console: bool = True,
) -> logging.Logger:
    """
    Initialize the logging infrastructure.

    Args:
        log_path: Path to the log file (e.g., 'logs/pipeline.log').
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        console: Whether to also log to stdout.

    Returns:
        The root logger instance.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(JSONFormatter())
    file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.addHandler(file_handler)

    # Console handler (optional)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logger.addHandler(console_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a named logger instance.

    Args:
        name: Logger name (e.g., 'main', 'adni_downloader').

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    event: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a structured event with optional data payload.

    Args:
        logger: The logger instance to use.
        event: Event name/description.
        data: Optional dictionary of event-specific data.
    """
    if data:
        logger.info(event, extra={"extra_data": data})
    else:
        logger.info(event)
