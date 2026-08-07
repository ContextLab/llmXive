"""
Structured logging utilities for the statistical robustness pipeline.

Provides a custom JSON formatter and helper functions to ensure consistent,
machine-parseable logging for warnings and errors across the project.
"""
import logging
import json
import sys
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class StructuredFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs log records as JSON.
    
    This ensures logs are machine-parseable and include structured metadata
    such as timestamp, level, logger name, and the message.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as a JSON string.
        
        Args:
            record: The logging record to format.
            
        Returns:
            A JSON string representing the log entry.
        """
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Include extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry["data"] = record.extra_data
        
        return json.dumps(log_entry)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configure and return a logger with structured JSON formatting.
    
    Args:
        name: The name of the logger (typically __name__).
        level: The logging level (e.g., logging.INFO, logging.WARNING).
        log_file: Optional path to a log file. If provided, logs are written there.
        console: If True, logs are also written to stdout.
        
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if logger is re-configured
    if logger.handlers:
        return logger
    
    formatter = StructuredFormatter()
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, creating it if necessary.
    
    Args:
        name: The name of the logger. If None, uses the root logger.
            
    Returns:
        A logger instance.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)


def _log_message(
    level: int,
    message: str,
    logger: Optional[logging.Logger] = None,
    **kwargs
) -> None:
    """
    Helper function to log a message with optional extra data.
    
    Args:
        level: The logging level.
        message: The log message.
        logger: The logger to use. If None, uses the root logger.
        kwargs: Additional key-value pairs to include in the log entry.
    """
    if logger is None:
        logger = logging.getLogger()
    
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    
    if kwargs:
        record.extra_data = kwargs
    
    logger.handle(record)


def log_info(message: str, logger: Optional[logging.Logger] = None, **kwargs) -> None:
    """Log an informational message."""
    _log_message(logging.INFO, message, logger, **kwargs)


def log_warning(message: str, logger: Optional[logging.Logger] = None, **kwargs) -> None:
    """Log a warning message."""
    _log_message(logging.WARNING, message, logger, **kwargs)


def log_error(message: str, logger: Optional[logging.Logger] = None, **kwargs) -> None:
    """Log an error message."""
    _log_message(logging.ERROR, message, logger, **kwargs)


def log_critical(message: str, logger: Optional[logging.Logger] = None, **kwargs) -> None:
    """Log a critical message."""
    _log_message(logging.CRITICAL, message, logger, **kwargs)


def log_debug(message: str, logger: Optional[logging.Logger] = None, **kwargs) -> None:
    """Log a debug message."""
    _log_message(logging.DEBUG, message, logger, **kwargs)
