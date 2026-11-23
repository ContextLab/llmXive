"""
Structured logging module with JSON output for pipeline traceability.
"""
import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Thread-local storage for loggers
_logger_registry = threading.local()


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, 'event_type'):
            log_data['event_type'] = record.event_type
        if hasattr(record, 'data'):
            log_data['data'] = record.data

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class PipelineLogger:
    """
    Thread-safe logger wrapper for pipeline operations.
    """

    def __init__(self, name: str, log_dir: Optional[Path] = None):
        """
        Initialize the pipeline logger.

        Args:
            name: Logger name
            log_dir: Directory for log files
        """
        self.name = name
        self.log_dir = log_dir or Path('logs')
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Get or create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(console_handler)

        # File handler
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = self.log_dir / f'{name}_{timestamp}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(file_handler)

    def log(self, level: int, message: str, **kwargs):
        """
        Log a message with optional extra fields.

        Args:
            level: Logging level
            message: Log message
            **kwargs: Extra fields to include in JSON
        """
        extra = kwargs.copy()
        extra['event_type'] = kwargs.pop('event_type', None)
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **kwargs):
        """Log INFO level message."""
        self.log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log WARNING level message."""
        self.log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log ERROR level message."""
        self.log(logging.ERROR, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log DEBUG level message."""
        self.log(logging.DEBUG, message, **kwargs)


def get_logger(name: str = __name__) -> PipelineLogger:
    """
    Get or create a pipeline logger.

    Args:
        name: Logger name

    Returns:
        PipelineLogger instance
    """
    if not hasattr(_logger_registry, 'loggers'):
        _logger_registry.loggers = {}

    if name not in _logger_registry.loggers:
        _logger_registry.loggers[name] = PipelineLogger(name)

    return _logger_registry.loggers[name]


def log_event(event_type: str, message: str, **kwargs):
    """
    Convenience function to log an event.

    Args:
        event_type: Type of event
        message: Log message
        **kwargs: Extra fields
    """
    logger = get_logger()
    logger.info(message, event_type=event_type, **kwargs)


def log_error(message: str, **kwargs):
    """
    Convenience function to log an error.

    Args:
        message: Error message
        **kwargs: Extra fields
    """
    logger = get_logger()
    logger.error(message, **kwargs)


def log_progress(stage: str, message: str, **kwargs):
    """
    Convenience function to log pipeline progress.

    Args:
        stage: Current stage
        message: Progress message
        **kwargs: Extra fields
    """
    logger = get_logger()
    logger.info(message, event_type=f'progress_{stage}', **kwargs)
