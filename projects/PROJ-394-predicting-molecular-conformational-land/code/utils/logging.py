"""
Structured logging utility for the molecular conformational landscape project.

Provides JSON-formatted logging to both file and console, with consistent
formatting and log level management.
"""

import logging
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional, Any, Dict

# Project root relative to this file
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
_LOG_DIR = os.path.join(_PROJECT_ROOT, 'data', 'logs')

# Ensure log directory exists
os.makedirs(_LOG_DIR, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None

class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

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

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def get_logger(name: str = "molecular_conformer") -> logging.Logger:
    """
    Returns a configured logger with JSON formatting for file and console output.

    Args:
        name: The name for the logger (default: "molecular_conformer").

    Returns:
        A configured logging.Logger instance.
    """
    global _logger

    if _logger is not None and _logger.name == name:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    log_file_path = os.path.join(_LOG_DIR, f"{name}.log")
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JsonFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _logger = logger
    return logger

def log_event(
    logger: logging.Logger,
    event_name: str,
    level: int = logging.INFO,
    **kwargs
) -> None:
    """
    Logs an event with structured data.

    Args:
        logger: The logger instance to use.
        event_name: The name of the event (will be part of the message).
        level: The log level (default: INFO).
        **kwargs: Additional key-value pairs to include in the JSON log.
    """
    extra_data = {"event": event_name, **kwargs}
    record = logger.makeRecord(
        logger.name, level, "", 0, event_name, (), None
    )
    record.extra_data = extra_data
    logger.handle(record)

# Convenience function to get the main project logger
def get_project_logger() -> logging.Logger:
    """Returns the main project logger."""
    return get_logger("molecular_conformer")

if __name__ == "__main__":
    # Example usage for testing
    log = get_project_logger()
    log.info("Logger initialized successfully.")
    log_event(log, "test_event", status="ok", details="Logging system is operational")
    log.debug("This is a debug message.")
    log.warning("This is a warning message.")
    try:
        1 / 0
    except ZeroDivisionError:
        log.error("An error occurred during test.", exc_info=True)