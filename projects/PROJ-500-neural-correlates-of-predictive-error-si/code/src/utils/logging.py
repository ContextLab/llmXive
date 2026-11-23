"""
Structured logging utilities for the llmXive pipeline.
Provides JSON-formatted logging for full pipeline traceability.
"""
import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

# Thread-local storage for loggers to ensure thread safety
_thread_local = threading.local()


class JsonFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs log records as JSON lines.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add standard logging attributes if they differ from defaults
        if record.lineno:
            log_data["lineno"] = record.lineno
        if record.pathname:
            log_data["file"] = os.path.basename(record.pathname)

        return json.dumps(log_data)


class PipelineLogger:
    """
    Thread-safe logger wrapper for the pipeline.
    Ensures consistent JSON formatting and provides convenience methods.
    """

    def __init__(self, name: str, log_file: Optional[Path] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers if logger already exists
        if not self.logger.handlers:
            # Console handler with JSON formatting
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(JsonFormatter())
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)

            # File handler if log_file is provided
            if log_file:
                log_file.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(log_file, mode='a')
                file_handler.setFormatter(JsonFormatter())
                file_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(file_handler)

    def log_event(self, event_type: str, message: str, **kwargs: Any) -> None:
        """
        Log a structured event with additional metadata.

        Args:
            event_type: Type of event (e.g., 'START', 'COMPLETE', 'ERROR')
            message: Human-readable message
            **kwargs: Additional metadata fields to include in the log
        """
        extra_fields = {"event_type": event_type, **kwargs}
        record = self.logger.makeRecord(
            self.name, logging.INFO, "", 0, message, (), None
        )
        record.extra_fields = extra_fields
        self.logger.handle(record)

    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs: Any) -> None:
        """
        Log an error message with optional exception details.

        Args:
            message: Error message
            error: Optional exception instance to include stack trace
            **kwargs: Additional metadata fields
        """
        extra_fields = {"event_type": "ERROR", **kwargs}
        record = self.logger.makeRecord(
            self.name, logging.ERROR, "", 0, message, (), error
        )
        record.extra_fields = extra_fields
        self.logger.handle(record)

    def log_progress(self, current: int, total: int, stage: str, **kwargs: Any) -> None:
        """
        Log progress for long-running operations.

        Args:
            current: Current step number
            total: Total number of steps
            stage: Name of the current stage
            **kwargs: Additional metadata fields
        """
        percent = (current / total * 100) if total > 0 else 0
        message = f"Progress: {current}/{total} ({percent:.1f}%) - {stage}"
        extra_fields = {
            "event_type": "PROGRESS",
            "current": current,
            "total": total,
            "stage": stage,
            "percent": percent,
            **kwargs
        }
        record = self.logger.makeRecord(
            self.name, logging.INFO, "", 0, message, (), None
        )
        record.extra_fields = extra_fields
        self.logger.handle(record)

    def get_logger(self) -> logging.Logger:
        """Return the underlying logging.Logger instance."""
        return self.logger


def get_logger(name: str = "pipeline", log_file: Optional[Path] = None) -> PipelineLogger:
    """
    Get or create a thread-safe PipelineLogger instance.

    Args:
        name: Name of the logger
        log_file: Optional path to write logs to disk

    Returns:
        PipelineLogger instance
    """
    # Use thread-local storage to ensure each thread gets its own logger instance
    if not hasattr(_thread_local, 'loggers'):
        _thread_local.loggers = {}

    if name not in _thread_local.loggers:
        _thread_local.loggers[name] = PipelineLogger(name, log_file)

    return _thread_local.loggers[name]


def log_event(message: str, event_type: str = "INFO", **kwargs: Any) -> None:
    """
    Convenience function to log an event using the default pipeline logger.

    Args:
        message: Log message
        event_type: Type of event
        **kwargs: Additional metadata
    """
    logger = get_logger()
    logger.log_event(event_type, message, **kwargs)


def log_error(message: str, error: Optional[Exception] = None, **kwargs: Any) -> None:
    """
    Convenience function to log an error using the default pipeline logger.

    Args:
        message: Error message
        error: Optional exception instance
        **kwargs: Additional metadata
    """
    logger = get_logger()
    logger.log_error(message, error, **kwargs)


def log_progress(current: int, total: int, stage: str, **kwargs: Any) -> None:
    """
    Convenience function to log progress using the default pipeline logger.

    Args:
        current: Current step
        total: Total steps
        stage: Stage name
        **kwargs: Additional metadata
    """
    logger = get_logger()
    logger.log_progress(current, total, stage, **kwargs)
