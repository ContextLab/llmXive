"""
Structured error logging module for the llmXive pipeline.

Implements FR-007 (Structured Logging) and FR-008 (Error Tracking).
Provides a consistent JSON-formatted logging interface for machine
parsing and human readability.
"""
import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum


class LogLevel(Enum):
    """Standard log levels matching Python's logging module."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON-structured log records.
    Ensures consistent format for downstream analysis and monitoring.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as a JSON string."""
        log_entry: Dict[str, Any] = {
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
        
        # Add extra context if available
        if hasattr(record, "extra_data"):
            log_entry["context"] = record.extra_data
        
        return json.dumps(log_entry)


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a configured logger instance with structured JSON output.
    
    Args:
        name: Logger name, typically the module name (__name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        
        # Console handler with structured formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(StructuredFormatter())
        
        logger.addHandler(console_handler)
    
    return logger


def log_error(
    logger: logging.Logger,
    message: str,
    error_code: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with structured context for error tracking (FR-008).
    
    Args:
        logger: Logger instance to use
        message: Error message
        error_code: Optional error code from error_codes.py
        context: Optional dictionary of contextual data
    """
    extra_context = {}
    if error_code:
        extra_context["error_code"] = error_code
    if context:
        extra_context.update(context)
    
    logger.error(
        message,
        extra={"extra_data": extra_context} if extra_context else {}
    )


def log_warning(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a warning with optional context.
    
    Args:
        logger: Logger instance
        message: Warning message
        context: Optional contextual data
    """
    logger.warning(
        message,
        extra={"extra_data": context} if context else {}
    )


def log_info(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log informational message with optional context.
    
    Args:
        logger: Logger instance
        message: Info message
        context: Optional contextual data
    """
    logger.info(
        message,
        extra={"extra_data": context} if context else {}
    )