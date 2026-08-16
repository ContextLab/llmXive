"""
Centralized logging configuration for the llmXive molecular polarity pipeline.

This module provides a standardized logging setup across all project modules.
It ensures consistent formatting, rotation, and JSON output for machine-readable logs.
"""
import logging
import json
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Global logger registry to prevent re-initialization
_loggers: Dict[str, logging.Logger] = {}

# Standard log format string
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# JSON formatter for structured logging
class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "pathname": record.pathname,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def get_project_root() -> Path:
    """Determine the project root directory."""
    current = Path(__file__).resolve()
    # Assume structure: code/utils/logging_config.py -> project root is parent of code/
    return current.parent.parent

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    json_logs: bool = False,
    console_output: bool = True,
) -> None:
    """
    Configure the root logger with standardized handlers and formatters.

    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Path to log file. If None, uses default logs/app.log
        json_logs: If True, use JSON formatting; otherwise use standard format
        console_output: If True, add a console handler
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Determine log file path
    if log_file is None:
        project_root = get_project_root()
        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir / "app.log")

    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Choose formatter
    formatter = JsonFormatter() if json_logs else logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # File handler with rotation (10MB max, 5 backup files)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the standardized configuration.

    Args:
        name: Logger name. If None, returns the root logger.

    Returns:
        Configured logger instance
    """
    if name is None:
        return logging.getLogger()

    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.propagate = False  # Prevent duplicate logs from root handler

    # If root logger isn't configured yet, set it up
    if not logging.getLogger().handlers:
        setup_logging()

    _loggers[name] = logger
    return logger

def set_log_level(level: int, logger_name: Optional[str] = None) -> None:
    """
    Set the log level for a specific logger or all loggers.

    Args:
        level: Logging level to set
        logger_name: Logger name. If None, sets level for root logger
    """
    if logger_name is None:
        logging.getLogger().setLevel(level)
    else:
        logger = get_logger(logger_name)
        logger.setLevel(level)
        # Also update handlers
        for handler in logger.handlers:
            handler.setLevel(level)

def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a message with additional context data.

    Args:
        logger: Logger instance to use
        level: Log level
        message: Log message
        context: Dictionary of additional context data to include
    """
    extra = {"extra_data": context} if context else {}
    logger.log(level, message, extra=extra)

# Initialize logging on module import for convenience
# This ensures logging is ready when any module imports this file
if not logging.getLogger().handlers:
    setup_logging()

__all__ = [
    "JsonFormatter",
    "get_logger",
    "set_log_level",
    "log_with_context",
    "setup_logging",
    "LOG_FORMAT",
    "DATE_FORMAT",
]
