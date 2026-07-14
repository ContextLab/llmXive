"""
Logging infrastructure for the llmXive pipeline.

Provides a JSON-formatted logger for pipeline monitoring, ensuring structured
logs that can be easily parsed for analysis and debugging.
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_config_summary, ensure_directories_exist


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""

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
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


def setup_logger(
    name: str = "llmXive_pipeline",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger with JSON formatting.

    Args:
        name: Logger name
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Path to log file. If None, logs only to console.
        console: Whether to log to console (stderr).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    formatter = JSONFormatter()

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        ensure_directories_exist(log_path.parent)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an event with optional structured data.

    Args:
        logger: Logger instance to use
        level: Logging level
        message: Log message
        data: Optional dictionary of structured data to include
    """
    extra = {}
    if data:
        extra["extra_data"] = data

    logger.log(level, message, extra=extra)


def log_pipeline_start(logger: logging.Logger, task_id: str) -> None:
    """Log the start of a pipeline task."""
    config_summary = get_config_summary()
    log_event(
        logger,
        logging.INFO,
        f"Pipeline task {task_id} started",
        {
            "task_id": task_id,
            "config": config_summary,
            "status": "started",
        },
    )


def log_pipeline_complete(
    logger: logging.Logger, task_id: str, duration_seconds: Optional[float] = None
) -> None:
    """Log the completion of a pipeline task."""
    log_event(
        logger,
        logging.INFO,
        f"Pipeline task {task_id} completed",
        {
            "task_id": task_id,
            "status": "completed",
            "duration_seconds": duration_seconds,
        },
    )


def log_pipeline_error(
    logger: logging.Logger, task_id: str, error_message: str
) -> None:
    """Log an error during pipeline execution."""
    log_event(
        logger,
        logging.ERROR,
        f"Pipeline task {task_id} failed",
        {
            "task_id": task_id,
            "status": "failed",
            "error": error_message,
        },
    )


# Default logger instance for general use
_default_logger: Optional[logging.Logger] = None


def get_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """Get or create the default logger instance."""
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger(
            name=name,
            log_file="data/validation/pipeline.log",
            console=True,
        )
    return _default_logger