import logging
import json
import sys
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Constants for context keys
CONTEXT_KEY = "context"
CORRELATION_ID_KEY = "correlation_id"
LEVEL_KEY = "level"
MESSAGE_KEY = "message"
TIMESTAMP_KEY = "timestamp"
MODULE_KEY = "module"
FUNCTION_KEY = "funcName"
LINE_KEY = "lineno"

class StructuredFormatter(logging.Formatter):
    """
    A custom formatter that outputs logs as JSON for structured logging.
    Includes correlation IDs, timestamps, and context.
    """
    def __init__(self, service_name: str = "alloy-design"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        # Generate a correlation ID if not present
        if not hasattr(record, CORRELATION_ID_KEY):
            setattr(record, CORRELATION_ID_KEY, str(uuid.uuid4()))

        log_entry = {
            TIMESTAMP_KEY: datetime.utcnow().isoformat() + "Z",
            LEVEL_KEY: record.levelname,
            MESSAGE_KEY: record.getMessage(),
            "service": self.service_name,
            "correlation_id": getattr(record, CORRELATION_ID_KEY, None),
            "module": record.module,
            FUNCTION_KEY: record.funcName,
            LINE_KEY: record.lineno,
        }

        # Add extra context if available
        if hasattr(record, CONTEXT_KEY):
            log_entry[CONTEXT_KEY] = getattr(record, CONTEXT_KEY)

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

class ContextFilter(logging.Filter):
    """
    A filter that adds a global correlation ID to all logs in a run.
    """
    def __init__(self):
        super().__init__()
        self.correlation_id = str(uuid.uuid4())

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, CORRELATION_ID_KEY):
            setattr(record, CORRELATION_ID_KEY, self.correlation_id)
        return True

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger configured with the structured formatter.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)
        logger.addFilter(ContextFilter())
    return logger

def configure_root_logger(service_name: str = "alloy-design", level: int = logging.INFO) -> None:
    """
    Configures the root logger with structured JSON output.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter(service_name=service_name))
    root_logger.addHandler(handler)
    
    # Add a global filter for correlation ID
    root_logger.addFilter(ContextFilter())

def log_error_with_context(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs an error message with optional structured context.
    """
    extra = {CONTEXT_KEY: context} if context else {}
    logger.error(message, extra=extra, exc_info=True)

def log_warning_with_context(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs a warning message with optional structured context.
    """
    extra = {CONTEXT_KEY: context} if context else {}
    logger.warning(message, extra=extra)

def log_info_with_context(logger: logging.Logger, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs an info message with optional structured context.
    """
    extra = {CONTEXT_KEY: context} if context else {}
    logger.info(message, extra=extra)