"""
Structured logging utility for the Brain Network Efficiency and Fluid Intelligence project.

Provides a centralized logging configuration that formats logs as JSON for
structured parsing, while maintaining human-readable output for local development.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = logging.INFO

# Global logger instance
_logger: Optional[logging.Logger] = None


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON for structured logging.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


def get_logger(name: str = "brain_network_efficiency") -> logging.Logger:
    """
    Get or create a configured logger instance.

    Args:
        name: The name for the logger (default: "brain_network_efficiency")

    Returns:
        A configured logger instance
    """
    global _logger

    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(DEFAULT_LOG_LEVEL)

        # Avoid adding handlers multiple times if this function is called repeatedly
        if not _logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(DEFAULT_LOG_LEVEL)

            # Check if we're running in a structured environment (CI, production)
            # by checking an environment variable
            import os
            is_structured = os.getenv("STRUCTURED_LOGGING", "false").lower() == "true"

            if is_structured:
                console_handler.setFormatter(StructuredFormatter())
            else:
                console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

            _logger.addHandler(console_handler)

    return _logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    **context: Any
) -> None:
    """
    Log a message with additional context data.

    Args:
        logger: The logger instance to use
        level: The logging level (e.g., logging.INFO, logging.ERROR)
        message: The log message
        **context: Additional context data to include in the log
    """
    record = logger.makeRecord(
        logger.name,
        level,
        "(unknown file)",
        0,
        message,
        (),
        None
    )
    record.extra_data = context
    logger.handle(record)


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[Path] = None,
    structured: bool = False
) -> logging.Logger:
    """
    Configure the root logger for the application.

    Args:
        log_level: Logging level as a string (e.g., "DEBUG", "INFO")
        log_file: Optional path to a log file
        structured: If True, use JSON formatting for all handlers

    Returns:
        The configured logger instance
    """
    global _logger

    if log_level:
        level = getattr(logging, log_level.upper(), DEFAULT_LOG_LEVEL)
    else:
        level = DEFAULT_LOG_LEVEL

    _logger = logging.getLogger("brain_network_efficiency")
    _logger.setLevel(level)

    # Clear existing handlers
    _logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if structured:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    _logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        if structured:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

        _logger.addHandler(file_handler)

    return _logger


# Convenience functions for common logging operations
def info(msg: str, **context: Any) -> None:
    """Log an info message with optional context."""
    logger = get_logger()
    if context:
        log_with_context(logger, logging.INFO, msg, **context)
    else:
        logger.info(msg)


def warning(msg: str, **context: Any) -> None:
    """Log a warning message with optional context."""
    logger = get_logger()
    if context:
        log_with_context(logger, logging.WARNING, msg, **context)
    else:
        logger.warning(msg)


def error(msg: str, **context: Any) -> None:
    """Log an error message with optional context."""
    logger = get_logger()
    if context:
        log_with_context(logger, logging.ERROR, msg, **context)
    else:
        logger.error(msg)


def debug(msg: str, **context: Any) -> None:
    """Log a debug message with optional context."""
    logger = get_logger()
    if context:
        log_with_context(logger, logging.DEBUG, msg, **context)
    else:
        logger.debug(msg)


def critical(msg: str, **context: Any) -> None:
    """Log a critical message with optional context."""
    logger = get_logger()
    if context:
        log_with_context(logger, logging.CRITICAL, msg, **context)
    else:
        logger.critical(msg)
