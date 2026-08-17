"""
Logging infrastructure for the Plant Disease Susceptibility project.

Provides structured logging, error tracking, and consistent log formatting
across the pipeline.
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import traceback
import os

# Global logger instance
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
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
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data)


class PlainTextFormatter(logging.Formatter):
    """Standard formatter for human-readable console output."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Custom format with timestamp, level, and message
        fmt = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def get_logger(name: str = "plant_disease") -> logging.Logger:
    """
    Get or create a logger with consistent configuration.
    
    Args:
        name: Logger name (default: "plant_disease")
    
    Returns:
        Configured logger instance
    """
    global _logger, _handler
    
    if _logger is None:
        _logger = logging.getLogger("plant_disease")
        _logger.setLevel(logging.DEBUG)
        
        # Avoid adding handlers multiple times
        if not _logger.handlers:
            # Console handler with plain text for readability
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(PlainTextFormatter())
            _logger.addHandler(console_handler)
            
            # File handler for structured logs (JSON)
            log_dir = Path("data/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"run_{timestamp}.jsonl"
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(JSONFormatter())
            _logger.addHandler(file_handler)
            
            _handler = file_handler
    
    return logging.getLogger(name)


def log_error(
    logger: logging.Logger, 
    message: str, 
    error: Optional[Exception] = None, 
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with optional exception details.
    
    Args:
        logger: Logger instance to use
        message: Error message
        error: Optional exception object to log details from
        extra: Optional dictionary of additional context
    """
    if error:
        logger.error(
            f"{message}: {str(error)}",
            exc_info=True,
            extra={"extra_fields": extra or {}}
        )
    else:
        logger.error(
            message,
            extra={"extra_fields": extra or {}}
        )


def log_warning(
    logger: logging.Logger,
    message: str,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a warning message with optional context.
    
    Args:
        logger: Logger instance to use
        message: Warning message
        extra: Optional dictionary of additional context
    """
    logger.warning(
        message,
        extra={"extra_fields": extra or {}}
    )


def log_info(
    logger: logging.Logger,
    message: str,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an informational message with optional context.
    
    Args:
        logger: Logger instance to use
        message: Info message
        extra: Optional dictionary of additional context
    """
    logger.info(
        message,
        extra={"extra_fields": extra or {}}
    )


def log_debug(
    logger: logging.Logger,
    message: str,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a debug message with optional context.
    
    Args:
        logger: Logger instance to use
        message: Debug message
        extra: Optional dictionary of additional context
    """
    logger.debug(
        message,
        extra={"extra_fields": extra or {}}
    )


def setup_logging_for_task(task_name: str) -> logging.Logger:
    """
    Set up a logger specifically for a task execution.
    
    Args:
        task_name: Name of the task (e.g., "T011_download_sra")
    
    Returns:
        Configured logger for the task
    """
    logger = get_logger(task_name)
    log_info(logger, f"Starting task: {task_name}")
    return logger


def close_logging() -> None:
    """Close all log handlers and flush buffers."""
    global _logger
    if _logger:
        for handler in _logger.handlers[:]:
            handler.close()
            _logger.removeHandler(handler)
    _logger = None
    _handler = None
