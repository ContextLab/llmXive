import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Constants
LOG_DIR = Path("results")
LOG_FILE_NAME = "pipeline.log"

def setup_logging(
    level: int = logging.INFO,
    log_to_console: bool = True,
    log_to_file: bool = True,
    log_dir: Optional[Path] = None,
) -> logging.Logger:
    """
    Configure structured JSON logging for the pipeline.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_to_console: Whether to log to stdout.
        log_to_file: Whether to log to a file in results/.
        log_dir: Directory for log files (default: results/).

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers

    if log_dir is None:
        log_dir = LOG_DIR

    # Ensure log directory exists
    if log_to_file:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / LOG_FILE_NAME

        # Create file handler
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    if log_to_console:
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(JsonFormatter())
        logger.addHandler(console_handler)

    return logger

class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as structured JSON.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)

def log_structured(
    logger: logging.Logger,
    level: int,
    msg: str,
    **kwargs: Any,
) -> None:
    """
    Log a message with additional structured data.

    Args:
        logger: The logger to use.
        level: Logging level.
        msg: The log message.
        **kwargs: Additional key-value pairs to include in the log.
    """
    extra = {"extra_data": kwargs}
    logger.log(level, msg, extra=extra)
