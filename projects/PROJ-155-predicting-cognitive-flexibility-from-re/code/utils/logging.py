"""
Logging utilities for structured logging of exclusions and errors.

This module provides a centralized logging configuration for the llmXive pipeline.
It ensures that all exclusions (e.g., motion, missing data) and critical errors
are logged in a structured format to specific files as required by the project specs.

Configuration:
  - Logs are written to `data/logs/exclusions.log` and `data/logs/errors.log`.
  - Uses JSON formatting for structured parsing.
  - Automatically creates the `data/logs` directory if it doesn't exist.
"""
import os
import logging
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List

from code.config import get_config
from code.data.paths import get_project_root, ensure_dir


# Global logger instance
_logger: Optional[logging.Logger] = None
_initialized: bool = False


class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
            "extra": {}
        }
        
        # Attach extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["extra"] = record.extra_data
        
        return json.dumps(log_entry)


def _create_file_handler(path: str, level: int = logging.INFO) -> logging.FileHandler:
    """Create a file handler with structured JSON formatting."""
    ensure_dir(os.path.dirname(path))
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(StructuredFormatter())
    return handler


def init_logging(debug: bool = False) -> logging.Logger:
    """
    Initialize the global logger with file handlers for exclusions and errors.
    
    Args:
        debug: If True, sets root logger level to DEBUG. Otherwise INFO.
    
    Returns:
        The configured logger instance.
    """
    global _logger, _initialized
    
    if _initialized:
        return _logger
    
    project_root = get_project_root()
    log_dir = os.path.join(project_root, "data", "logs")
    ensure_dir(log_dir)
    
    exclusions_path = os.path.join(log_dir, "exclusions.log")
    errors_path = os.path.join(log_dir, "errors.log")
    
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    _logger.handlers.clear()
    
    # Exclusion logger (INFO level)
    exc_handler = _create_file_handler(exclusions_path, logging.INFO)
    exc_handler.addFilter(lambda record: record.levelno >= logging.INFO and 
                                   hasattr(record, "is_exclusion") and record.is_exclusion)
    _logger.addHandler(exc_handler)
    
    # Error logger (ERROR level)
    err_handler = _create_file_handler(errors_path, logging.ERROR)
    err_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
    _logger.addHandler(err_handler)
    
    # Console handler for general output (optional, for debugging)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    _logger.addHandler(console_handler)
    
    _initialized = True
    return _logger


def log_exclusion(subject_id: str, reason: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a subject exclusion event.
    
    Args:
        subject_id: The ID of the excluded subject.
        reason: The reason for exclusion (e.g., "Motion", "Missing_Behavioral_Score").
        details: Optional dictionary of additional context (e.g., Mean_FD value).
    """
    if _logger is None:
        init_logging()
    
    extra_data = details or {}
    extra_data["subject_id"] = subject_id
    extra_data["reason"] = reason
    
    record = _logger.makeRecord(
        _logger.name, 
        logging.INFO, 
        "", 
        0, 
        f"Excluded subject {subject_id}: {reason}", 
        (), 
        None
    )
    record.is_exclusion = True
    record.extra_data = extra_data
    
    _logger.handle(record)


def log_error(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error event.
    
    Args:
        message: The error message.
        context: Optional dictionary of additional context.
    """
    if _logger is None:
        init_logging()
    
    extra_data = context or {}
    
    record = _logger.makeRecord(
        _logger.name, 
        logging.ERROR, 
        "", 
        0, 
        message, 
        (), 
        None
    )
    record.extra_data = extra_data
    
    _logger.handle(record)


def log_warning(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a warning event.
    
    Args:
        message: The warning message.
        context: Optional dictionary of additional context.
    """
    if _logger is None:
        init_logging()
    
    extra_data = context or {}
    _logger.warning(message, extra={"extra_data": extra_data})


def get_exclusion_log_path() -> str:
    """Return the path to the exclusions log file."""
    project_root = get_project_root()
    return os.path.join(project_root, "data", "logs", "exclusions.log")


def get_error_log_path() -> str:
    """Return the path to the errors log file."""
    project_root = get_project_root()
    return os.path.join(project_root, "data", "logs", "errors.log")