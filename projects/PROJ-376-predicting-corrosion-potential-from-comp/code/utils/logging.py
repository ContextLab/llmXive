"""
Logging infrastructure setup for the corrosion prediction pipeline.
Implements FR-010: Reproducible logging with timestamps, levels, and structured JSON‑line output.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Global logger registry to prevent duplicate handlers
_loggers = {}
_log_level = logging.INFO

# Default log directory (relative to project root)
# This aligns with T001 setup: data/logs/
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_LOG_FILE = "pipeline.log"


class JsonLogFormatter(logging.Formatter):
    """
    Formatter that outputs a JSON object per log record.
    Fields:
        timestamp: ISO‑8601 UTC timestamp
        logger:   logger name
        level:    log level name (e.g., INFO)
        message:  the log message
    """

    def format(self, record: logging.LogRecord) -> str:
        # Ensure timestamp is in UTC ISO format with seconds precision
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        log_entry = {
            "timestamp": ts,
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True,
) -> logging.Logger:
    """
    Setup a logger with optional file and console handlers.
    Ensures reproducible formatting and prevents duplicate handlers.

    Args:
        name: Logger name (usually __name__).
        log_file: Path to log file relative to project root.
                  If None, no file handler is added.
        level: Logging level.
        console: Whether to also log to stdout.

    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Remove any existing handlers (important for re‑runs in tests)
    logger.handlers.clear()

    # Use JSON formatter for both console and file to keep output consistent
    json_formatter = JsonLogFormatter()

    # Console handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(json_formatter)
        logger.addHandler(ch)

    # File handler
    if log_file:
        # Resolve relative paths against the current working directory (project root)
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = Path.cwd() / log_path
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(str(log_path), encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(json_formatter)
        logger.addHandler(fh)

    _loggers[name] = logger
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger, creating it with default settings if necessary.
    Default settings log to ``data/logs/pipeline.log`` and to the console.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    default_log_path = DEFAULT_LOG_DIR / DEFAULT_LOG_FILE
    return setup_logger(
        name,
        log_file=str(default_log_path),
        console=True,
        level=_log_level,
    )


def log_message(
    logger_name: str,
    message: str,
    level: int = logging.INFO,
) -> None:
    """
    Convenience wrapper to log a message using the named logger.

    Args:
        logger_name: Name of the logger.
        message: Message to log.
        level: Logging level (e.g., ``logging.INFO``).
    """
    logger = get_logger(logger_name)
    logger.log(level, message)


def set_global_log_level(level: int) -> None:
    """
    Set the global logging level for all subsequently created loggers.

    Args:
        level: Logging level (e.g., ``logging.DEBUG``).
    """
    global _log_level
    _log_level = level
