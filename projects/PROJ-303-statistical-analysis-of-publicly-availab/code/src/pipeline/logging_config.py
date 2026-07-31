import logging
import logging.handlers
import os
import sys
import json
import traceback
import time
from typing import Optional, Dict, Any
from functools import wraps
from pathlib import Path

# Ensure the logs directory exists
LOG_DIR = Path("state/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger registry to prevent duplicate handlers
_logger_registry: Dict[str, bool] = {}

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Includes timestamp, level, name, message, and optional extra context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%f"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": "".join(traceback.format_exception(*record.exc_info))
            }

        # Add any extra fields passed in the log call
        if hasattr(record, 'context'):
            log_data["context"] = record.context

        return json.dumps(log_data)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves or creates a logger with consistent configuration.
    Configures console and file handlers with JSON formatting.
    """
    logger = logging.getLogger(name)
    
    # Avoid re-adding handlers if already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File Handler (rotating file)
    log_file_path = LOG_DIR / f"{name}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    return logger

def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Centralized error handler that logs the exception with context
    and potentially performs cleanup or fallback actions.
    """
    logger = get_logger()
    log_entry = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc()
    }
    if context:
        log_entry["context"] = context
    
    logger.error("Unhandled error occurred", extra={"context": log_entry}, exc_info=True)
    raise error

def log_with_context(logger_name: str, message: str, level: int = logging.INFO, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs a message with additional context data.
    """
    logger = get_logger(logger_name)
    log_method = getattr(logger, {
        logging.DEBUG: "debug",
        logging.INFO: "info",
        logging.WARNING: "warning",
        logging.ERROR: "error",
        logging.CRITICAL: "critical"
    }.get(level, "info"))
    
    log_method(message, extra={"context": context} if context else {})

def time_execution(func):
    """
    Decorator to log the execution time of a function.
    Logs start, end, and duration in seconds.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        logger.info(f"Starting execution of {func.__name__}", extra={"context": {"function": func.__name__}})
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Completed execution of {func.__name__}", extra={
                "context": {
                    "function": func.__name__,
                    "duration_seconds": round(duration, 4),
                    "status": "success"
                }
            })
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Failed execution of {func.__name__}", extra={
                "context": {
                    "function": func.__name__,
                    "duration_seconds": round(duration, 4),
                    "status": "failed",
                    "error": str(e)
                }
            }, exc_info=True)
            raise
    return wrapper
