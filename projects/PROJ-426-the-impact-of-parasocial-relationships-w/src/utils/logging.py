"""
Structured logging and progress tracking utilities for the llmXive pipeline.

This module provides a consistent logging configuration that outputs structured
JSON logs for machine parsing and human-readable logs for development.
It also includes progress tracking utilities for long-running data processing tasks.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import os

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT_JSON = "json"
LOG_FORMAT_TEXT = "text"

# Global logger instance
_logger: Optional[logging.Logger] = None
_progress_bar_enabled: bool = True


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""
    
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
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry)


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_format: str = LOG_FORMAT_JSON,
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> logging.Logger:
    """
    Configure and return the project logger.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_format: Either 'json' or 'text'
        log_file: Optional path to write logs to file
        enable_console: Whether to log to stdout/stderr
        
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(log_level)
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Create formatter
    if log_format == LOG_FORMAT_JSON:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Add console handler if requested
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    return _logger


def get_logger() -> logging.Logger:
    """
    Get the configured logger instance.
    
    Returns:
        Logger instance, or a default logger if not configured yet.
    """
    global _logger
    
    if _logger is None:
        # Initialize with defaults if not set up
        _logger = setup_logging()
    
    return _logger


def log_progress(
    message: str,
    current: int,
    total: int,
    unit: str = "items",
    level: int = logging.INFO
) -> None:
    """
    Log progress for long-running operations.
    
    Args:
        message: Description of the operation
        current: Current progress count
        total: Total count
        unit: Unit of measurement (e.g., 'records', 'users')
        level: Logging level
    """
    logger = get_logger()
    progress_pct = (current / total * 100) if total > 0 else 0
    
    log_entry = {
        "type": "progress",
        "message": message,
        "current": current,
        "total": total,
        "unit": unit,
        "percentage": round(progress_pct, 2)
    }
    
    # Create a log record with extra fields
    record = logger.makeRecord(
        logger.name,
        level,
        "",
        0,
        f"{message}: {current}/{total} ({progress_pct:.2f}%)",
        (),
        None
    )
    record.extra_fields = log_entry
    logger.handle(record)


def log_data_stats(
    source: str,
    record_count: int,
    columns: Optional[list] = None,
    missing_values: Optional[Dict[str, int]] = None,
    duplicates: Optional[int] = None
) -> None:
    """
    Log structured data statistics for validation and debugging.
    
    Args:
        source: Name of the data source
        record_count: Total number of records
        columns: List of column names (optional)
        missing_values: Dict of column -> missing count (optional)
        duplicates: Number of duplicate records (optional)
    """
    logger = get_logger()
    
    stats = {
        "type": "data_stats",
        "source": source,
        "record_count": record_count
    }
    
    if columns:
        stats["columns"] = columns
    if missing_values:
        stats["missing_values"] = missing_values
    if duplicates is not None:
        stats["duplicates"] = duplicates
    
    # Create log record with stats
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        f"Data stats for {source}: {record_count} records",
        (),
        None
    )
    record.extra_fields = stats
    logger.handle(record)


def log_error_context(
    message: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with additional context information.
    
    Args:
        message: Error message
        error: The exception that occurred
        context: Additional context data (optional)
    """
    logger = get_logger()
    
    log_entry = {
        "type": "error",
        "message": message,
        "error_type": type(error).__name__,
        "error_message": str(error)
    }
    
    if context:
        log_entry["context"] = context
    
    # Create log record with exception and extra fields
    record = logger.makeRecord(
        logger.name,
        logging.ERROR,
        "",
        0,
        message,
        (),
        error
    )
    record.extra_fields = log_entry
    logger.handle(record)


# Convenience functions for common logging patterns
def info(msg: str, **kwargs) -> None:
    """Log an info message with optional extra fields."""
    logger = get_logger()
    if kwargs:
        record = logger.makeRecord(logger.name, logging.INFO, "", 0, msg, (), None)
        record.extra_fields = kwargs
        logger.handle(record)
    else:
        logger.info(msg)

def debug(msg: str, **kwargs) -> None:
    """Log a debug message with optional extra fields."""
    logger = get_logger()
    if kwargs:
        record = logger.makeRecord(logger.name, logging.DEBUG, "", 0, msg, (), None)
        record.extra_fields = kwargs
        logger.handle(record)
    else:
        logger.debug(msg)

def warning(msg: str, **kwargs) -> None:
    """Log a warning message with optional extra fields."""
    logger = get_logger()
    if kwargs:
        record = logger.makeRecord(logger.name, logging.WARNING, "", 0, msg, (), None)
        record.extra_fields = kwargs
        logger.handle(record)
    else:
        logger.warning(msg)

def error(msg: str, **kwargs) -> None:
    """Log an error message with optional extra fields."""
    logger = get_logger()
    if kwargs:
        record = logger.makeRecord(logger.name, logging.ERROR, "", 0, msg, (), None)
        record.extra_fields = kwargs
        logger.handle(record)
    else:
        logger.error(msg)