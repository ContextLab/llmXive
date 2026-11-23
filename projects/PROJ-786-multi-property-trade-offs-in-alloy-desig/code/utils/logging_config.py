import logging
import json
import sys
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

# Global logger instance
_logger: Optional[logging.Logger] = None

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs JSON structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "trace_id": getattr(record, "trace_id", None),
            "context": getattr(record, "context", {}),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

class ContextFilter(logging.Filter):
    """Filter to add context to log records."""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        record.context = {**self.context, **getattr(record, "context", {})}
        return True

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get or create a logger with the specified name."""
    global _logger
    if _logger is None:
        _logger = configure_root_logger()
    return logging.getLogger(name)

def configure_root_logger(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """Configure the root logger with JSON formatting and file rotation."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)

    # File handler with rotation if log_file is provided
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)

    return root_logger

def log_info_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Log an info message with optional context and trace ID."""
    extra = {"context": context or {}, "trace_id": trace_id or str(uuid.uuid4())}
    logger.info(message, extra=extra)

def log_warning_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Log a warning message with optional context and trace ID."""
    extra = {"context": context or {}, "trace_id": trace_id or str(uuid.uuid4())}
    logger.warning(message, extra=extra)

def log_error_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Log an error message with optional context and trace ID."""
    extra = {"context": context or {}, "trace_id": trace_id or str(uuid.uuid4())}
    logger.error(message, extra=extra)

def log_critical_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Log a critical message with optional context and trace ID."""
    extra = {"context": context or {}, "trace_id": trace_id or str(uuid.uuid4())}
    logger.critical(message, extra=extra)

def log_debug_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
) -> None:
    """Log a debug message with optional context and trace ID."""
    extra = {"context": context or {}, "trace_id": trace_id or str(uuid.uuid4())}
    logger.debug(message, extra=extra)
