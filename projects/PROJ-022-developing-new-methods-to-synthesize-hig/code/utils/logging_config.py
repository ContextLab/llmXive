"""
Logging configuration for the llmXive membrane synthesis pipeline.
Provides structured JSON logging and standardized logger setup across all stages.
"""
import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, Union

# Custom JSON formatter for structured logging
class StructuredFormatter(logging.Formatter):
    """
    Formats log records as JSON lines for structured logging.
    Includes timestamp, level, logger name, message, and optional extra context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        # Add extra context if present
        if hasattr(record, "extra_data"):
            log_entry["extra"] = record.extra_data

        return json.dumps(log_entry)

def get_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = False,
    log_file_path: Optional[str] = None
) -> logging.Logger:
    """
    Get or create a logger with structured JSON formatting.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_to_file: Whether to also log to a file
        log_file_path: Path to the log file (required if log_to_file is True)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Console handler with structured formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)

    # Optional file handler
    if log_to_file:
        if not log_file_path:
            raise ValueError("log_file_path must be provided when log_to_file is True")

        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)

    return logger

def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    level: int = logging.INFO,
    **kwargs: Any
) -> None:
    """
    Log a structured event with additional context.

    Args:
        logger: The logger to use
        event_type: Type of event (e.g., 'START', 'COMPLETE', 'ERROR')
        message: Human-readable message
        level: Log level
        **kwargs: Additional context to include in the log
    """
    extra_data = {
        "event_type": event_type,
        **kwargs
    }
    logger.log(level, message, extra={"extra_data": extra_data})

def setup_pipeline_logger(
    name: str = "pipeline",
    log_level: str = "INFO",
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    Set up the main pipeline logger with appropriate level and optional file logging.

    Args:
        name: Logger name
        log_level: Log level as string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_dir: Directory to store log files (if None, only console logging is used)

    Returns:
        Configured pipeline logger
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    level = level_map.get(log_level.upper(), logging.INFO)

    log_file_path = None
    if log_dir:
        import os
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_path = os.path.join(log_dir, f"{name}_{timestamp}.log")

    return get_logger(
        name=name,
        level=level,
        log_to_file=log_file_path is not None,
        log_file_path=log_file_path
    )