"""
Logging configuration for the llmXive research pipeline.

Sets up a rotating file handler to write JSON-formatted logs to
artifacts/logs/app.log with DEBUG level.
"""
import logging
import os
import json
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

# Ensure the logs directory exists
LOG_DIR = Path(__file__).parent.parent / "artifacts" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""

    def format(self, record):
        log_record = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


def setup_logging(level=logging.DEBUG):
    """
    Configure the root logger with a rotating file handler and JSON formatting.

    Args:
        level: The logging level (default: DEBUG).
    """
    # Prevent adding multiple handlers if called multiple times
    if any(isinstance(h, RotatingFileHandler) for h in logging.root.handlers):
        return

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create rotating file handler
    # Max size 10MB, keep 5 backup files
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(level)

    # Set formatter
    formatter = JsonFormatter()
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    # Optional: Add a console handler for immediate feedback during development
    # Uncomment if console output is desired
    # console_handler = logging.StreamHandler()
    # console_handler.setLevel(logging.INFO)
    # console_handler.setFormatter(JsonFormatter())
    # logger.addHandler(console_handler)

# Initialize logging immediately upon import
setup_logging()
