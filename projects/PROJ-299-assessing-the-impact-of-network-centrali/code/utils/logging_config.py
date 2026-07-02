"""
Logging infrastructure for the llmXive pipeline.

Implements FR-011: Machine-readable logs in JSON format.
Logs are written to logs/pipeline.log.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure the logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE_PATH = LOGS_DIR / "pipeline.log"

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""

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
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.
    
    Args:
        log_file: Path to the log file. Defaults to logs/pipeline.log.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console_output: Whether to also output logs to stdout/stderr.
        
    Returns:
        The configured root logger.
    """
    if log_file is None:
        log_file = LOG_FILE_PATH
    
    # Ensure parent directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler with JSON formatting
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # Console handler for immediate feedback (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        # Use a simple text format for console to be human-readable
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.
    
    Args:
        name: Name of the logger (usually __name__).
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an event with optional structured data.
    
    Args:
        logger: The logger instance to use.
        level: The logging level.
        message: The log message.
        extra_data: Optional dictionary of key-value pairs to include in the JSON log.
    """
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        message,
        (),
        None,
        func=""
    )
    if extra_data:
        record.extra_data = extra_data
    logger.handle(record)
