import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

LOG_FILE_PATH = "data/processed/execution.log"


class JSONFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with JSON formatting.
    Ensures the log directory exists.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Ensure directory exists
    log_dir = os.path.dirname(LOG_FILE_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    # File handler
    try:
        fh = logging.FileHandler(LOG_FILE_PATH)
        fh.setFormatter(JSONFormatter())
        logger.addHandler(fh)
    except Exception:
        # Fallback to stderr if file logging fails
        pass

    # Console handler (optional, for debugging)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(JSONFormatter())
    logger.addHandler(ch)

    return logger


def get_task_logger(task_name: str) -> logging.Logger:
    """Get a logger specifically for a task context."""
    return get_logger(f"llmXive.{task_name}")


def log_error(logger: logging.Logger, message: str, exc: Optional[Exception] = None):
    """Log an error message, optionally with exception info."""
    if exc:
        logger.error(message, exc_info=True)
    else:
        logger.error(message)


def log_with_context(
    logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None
):
    """Log a message with additional context data."""
    if context:
        full_message = f"{message} | Context: {json.dumps(context)}"
        logger.info(full_message)
    else:
        logger.info(message)


def log_task_start(logger: logging.Logger, task_id: str):
    """Log the start of a task."""
    logger.info(f"Task {task_id} started at {datetime.now(timezone.utc).isoformat()}")


def log_task_complete(logger: logging.Logger, task_id: str):
    """Log the completion of a task."""
    logger.info(f"Task {task_id} completed at {datetime.now(timezone.utc).isoformat()}")


def log_task_failed(logger: logging.Logger, task_id: str, reason: str):
    """Log a task failure."""
    logger.error(f"Task {task_id} failed: {reason}")
