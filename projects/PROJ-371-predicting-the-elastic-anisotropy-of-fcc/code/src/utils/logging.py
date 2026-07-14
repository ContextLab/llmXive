import logging
import json
import sys
from datetime import datetime
from typing import Optional, Any, Dict
import traceback

from .config import get_path


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        return json.dumps(log_data)


def setup_logger(
    name: str = "elastic_anisotropy",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger with optional JSON file handler and console handler.

    Args:
        name: Logger name.
        level: Logging level (e.g., logging.INFO).
        log_file: Optional path to log file. If provided, logs are saved as JSON lines.
        console: Whether to log to console.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers

    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    if log_file:
        log_path = get_path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "elastic_anisotropy") -> logging.Logger:
    """
    Retrieve an existing logger or create a new one with default settings.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Default to console logging if not configured
        setup_logger(name, console=True)
    return logger


def log_error(
    message: str,
    logger_name: str = "elastic_anisotropy",
    exc_info: bool = True,
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an error message."""
    logger = get_logger(logger_name)
    record = logger.makeRecord(
        logger.name, logging.ERROR, "", 0, message, (), None
    )
    if extra_data:
        record.extra_data = extra_data
    logger.handle(record)
    if exc_info:
        logger.exception(message)


def log_warning(
    message: str,
    logger_name: str = "elastic_anisotropy",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a warning message."""
    logger = get_logger(logger_name)
    record = logger.makeRecord(
        logger.name, logging.WARNING, "", 0, message, (), None
    )
    if extra_data:
        record.extra_data = extra_data
    logger.handle(record)


def log_info(
    message: str,
    logger_name: str = "elastic_anisotropy",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log an info message."""
    logger = get_logger(logger_name)
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, message, (), None
    )
    if extra_data:
        record.extra_data = extra_data
    logger.handle(record)


def log_debug(
    message: str,
    logger_name: str = "elastic_anisotropy",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a debug message."""
    logger = get_logger(logger_name)
    record = logger.makeRecord(
        logger.name, logging.DEBUG, "", 0, message, (), None
    )
    if extra_data:
        record.extra_data = extra_data
    logger.handle(record)


def log_success(
    message: str,
    logger_name: str = "elastic_anisotropy",
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Log a success message (custom level or INFO)."""
    logger = get_logger(logger_name)
    # Map success to INFO level for standard compliance, or use a custom level if needed
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0, f"[SUCCESS] {message}", (), None
    )
    if extra_data:
        record.extra_data = extra_data
    logger.handle(record)
