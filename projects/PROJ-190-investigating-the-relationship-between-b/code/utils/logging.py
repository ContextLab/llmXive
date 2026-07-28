"""
Structured logging utilities for the pipeline.

Provides consistent logging format with context information for debugging
and auditing purposes.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from config import PROJECT_ROOT


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "context"):
            log_entry["context"] = record.context

        return json.dumps(log_entry)


def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None,
    json_format: bool = True
) -> None:
    """
    Configure logging for the entire application.

    Args:
        log_level: Logging level (default INFO)
        log_file: Optional path to log file
        json_format: If True, use structured JSON format (default True)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if json_format:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(StructuredFormatter() if json_format else logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        root_logger.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a message with optional context.

    Args:
        logger: Logger instance
        level: Log level
        message: Message to log
        context: Optional context dictionary
    """
    extra = {"context": context} if context else {}
    logger.log(level, message, extra=extra)


# Convenience functions
def info(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an info message."""
    log_with_context(logger, logging.INFO, message, context)


def warning(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a warning message."""
    log_with_context(logger, logging.WARNING, message, context)


def error(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an error message."""
    log_with_context(logger, logging.ERROR, message, context)


def debug(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a debug message."""
    log_with_context(logger, logging.DEBUG, message, context)


def critical(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """Log a critical message."""
    log_with_context(logger, logging.CRITICAL, message, context)
