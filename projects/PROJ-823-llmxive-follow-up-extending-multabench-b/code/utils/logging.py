"""
Structured logging utilities for the llmXive pipeline.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logging(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    use_json: bool = True
) -> logging.Logger:
    """
    Set up a logger with optional file and console handlers.
    
    Args:
        name: Name of the logger.
        level: Logging level.
        log_file: Optional path to a log file.
        use_json: If True, use JSON formatting.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    formatter = StructuredFormatter() if use_json else logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.setLevel(level)
    logger.addHandler(ch)

    # File Handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance, creating it if it doesn't exist.
    """
    return logging.getLogger(name)

def log_info(logger: logging.Logger, message: str, **kwargs):
    """Log an info message with optional extra context."""
    extra = {"context": kwargs} if kwargs else {}
    logger.info(message, extra=extra)

def log_warning(logger: logging.Logger, message: str, **kwargs):
    """Log a warning message with optional extra context."""
    extra = {"context": kwargs} if kwargs else {}
    logger.warning(message, extra=extra)

def log_error(logger: logging.Logger, message: str, **kwargs):
    """Log an error message with optional extra context."""
    extra = {"context": kwargs} if kwargs else {}
    logger.error(message, extra=extra)

def log_debug(logger: logging.Logger, message: str, **kwargs):
    """Log a debug message with optional extra context."""
    extra = {"context": kwargs} if kwargs else {}
    logger.debug(message, extra=extra)

def log_critical(logger: logging.Logger, message: str, **kwargs):
    """Log a critical message with optional extra context."""
    extra = {"context": kwargs} if kwargs else {}
    logger.critical(message, extra=extra)

def log_exception(logger: logging.Logger, message: str, exc_info: bool = True):
    """Log an exception message."""
    logger.exception(message, exc_info=exc_info)

def log_event(logger: logging.Logger, event_type: str, data: Dict[str, Any]):
    """Log a structured event."""
    logger.info(json.dumps({"event": event_type, "data": data}))