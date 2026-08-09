"""
Logging infrastructure for the llmXive pipeline.
Implements FR-011: Machine-readable JSON logs.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler

# Ensure log directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "pipeline.log"

class JSONFormatter(logging.Formatter):
    """
    Formats log records as JSON lines (machine-readable).
    Includes timestamp, level, logger name, message, and optional extra context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
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
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to the log file. Defaults to logs/pipeline.log.
        console_output: If True, also log to stderr.

    Returns:
        The root logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    target_file = log_file or LOG_FILE

    # Ensure parent directory exists
    target_file.parent.mkdir(parents=True, exist_ok=True)

    # File handler with rotation (10MB max, 5 backups)
    file_handler = RotatingFileHandler(
        target_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())

    logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        # Console can use human-readable format for debugging
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    Uses the root logger's configuration.
    """
    return logging.getLogger(name)

def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    **kwargs: Any
) -> None:
    """
    Log an event with optional structured context.

    Args:
        logger: The logger instance.
        level: Log level.
        message: The log message.
        **kwargs: Additional key-value pairs to include in the JSON log entry.
    """
    extra = {"extra_data": kwargs} if kwargs else {}
    logger.log(level, message, extra=extra)
