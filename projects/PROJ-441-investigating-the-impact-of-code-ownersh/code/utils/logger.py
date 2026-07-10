import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time

# Ensure the logs directory exists
LOG_DIR = Path("data") / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default log file path
DEFAULT_LOG_FILE = LOG_DIR / "pipeline.log"

# Log rotation settings
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance with structured JSON formatting
    and file rotation.
    """
    global _logger
    if _logger is not None:
        return _logger

    # Create logger
    _logger = logging.getLogger(name)
    _logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if called multiple times
    if _logger.handlers:
        return _logger

    # Formatter for structured logging (JSON-like)
    class StructuredFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data: Dict[str, Any] = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created)),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            # Add extra fields if present
            if hasattr(record, "extra_data"):
                log_data.update(record.extra_data)
            return json.dumps(log_data)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    _logger.addHandler(console_handler)

    # File handler with rotation
    if DEFAULT_LOG_FILE.exists():
        # Ensure file exists for rotation to work correctly
        pass

    file_handler = RotatingFileHandler(
        str(DEFAULT_LOG_FILE),
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredFormatter())
    _logger.addHandler(file_handler)

    return _logger

def log_event(
    message: str,
    level: str = "INFO",
    extra_data: Optional[Dict[str, Any]] = None,
    logger_name: str = "llmXive",
) -> None:
    """
    Logs an event with optional extra structured data.
    """
    logger = get_logger(logger_name)
    log_record = logging.LogRecord(
        name=logger_name,
        level=getattr(logging, level.upper(), logging.INFO),
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    if extra_data:
        log_record.extra_data = extra_data
    logger.handle(log_record)

def init_logger() -> None:
    """
    Explicitly initializes the logger. Can be called at startup.
    """
    get_logger()
    log_event("Logger initialized", "INFO", {"path": str(DEFAULT_LOG_FILE)})

# Initialize on import
init_logger()
