import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

class JSONFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records as JSON lines.
    This ensures machine-readable logs as required by FR-011.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
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

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def setup_logging(
    log_file: Optional[Path] = None,
    log_level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.

    Args:
        log_file: Path to the log file (e.g., logs/pipeline.log).
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        console_output: Whether to also log to stdout/stderr.

    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Ensure log directory exists if a file path is provided
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        # For console, use a human-readable format for debugging
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger that inherits configuration from the root logger.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        A logger instance.
    """
    return logging.getLogger(name)

def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    **extra_data
) -> None:
    """
    Log an event with optional extra data fields attached to the log record.

    Args:
        logger: The logger instance to use.
        level: The logging level.
        message: The log message.
        **extra_data: Additional key-value pairs to include in the JSON log.
    """
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        message,
        (),
        None
    )
    if extra_data:
        record.extra_data = extra_data
    logger.handle(record)
