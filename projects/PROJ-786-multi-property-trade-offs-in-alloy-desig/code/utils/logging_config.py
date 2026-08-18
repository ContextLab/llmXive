"""
Logging infrastructure for llmXive Alloy Design project.
Provides structured JSON logging, context filters, and utility functions.
"""
import logging
import json
import sys
import uuid
import os
from datetime import datetime
from typing import Optional, Dict, Any
from logging import Filter, LogRecord

class StructuredFormatter(logging.Formatter):
    """
    Formats log records as JSON for structured logging.
    Includes timestamp, level, message, module, line, and optional context.
    """
    def format(self, record: LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": os.getpid(),
            "thread_id": record.thread,
            "request_id": getattr(record, 'request_id', None),
            "task_id": getattr(record, 'task_id', None),
            "context": getattr(record, 'context', {}),
            "exception": None
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

class ContextFilter(Filter):
    """
    Filter that injects global context (e.g., run_id, project_id) into every log record.
    """
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record: LogRecord) -> bool:
        # Inject global context
        if self.context:
            if not hasattr(record, 'context'):
                record.context = {}
            record.context.update(self.context)
        return True

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a logger instance configured with the structured formatter.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        configure_root_logger()
    return logger

def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger with a StreamHandler and StructuredFormatter.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())

    # Add global context filter (can be extended with project-specific context)
    context_filter = ContextFilter({
        "project_id": "PROJ-786-multi-property-trade-offs-in-alloy-desig",
        "run_id": str(uuid.uuid4())[:8]
    })
    handler.addFilter(context_filter)

    root_logger.addHandler(handler)

def log_info_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log an info message with additional context data.
    """
    extra = {"context": context or {}}
    extra.update(kwargs)
    logger.info(message, extra=extra)

def log_warning_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    **kwargs
) -> None:
    """
    Log a warning message with additional context data.
    """
    extra = {"context": context or {}}
    extra.update(kwargs)
    logger.warning(message, extra=extra)

def log_error_with_context(
    logger: logging.Logger,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    exc_info: bool = True,
    **kwargs
) -> None:
    """
    Log an error message with additional context data and optional exception info.
    """
    extra = {"context": context or {}}
    extra.update(kwargs)
    logger.error(message, extra=extra, exc_info=exc_info)

# Initialize root logger on module import
configure_root_logger()
