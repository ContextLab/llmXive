"""
Structured logging module for the llmXive pipeline.

Provides a singleton-configured JSON logger for pipeline traceability.
All logs are written to JSON Lines format for easy parsing and auditing.
"""
import json
import logging
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.config import get_config


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON Lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present in the record
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)


class PipelineLogger:
    """
    Singleton-style logger wrapper for the research pipeline.

    Ensures consistent JSON formatting and output destination across the project.
    """

    _instance: Optional["PipelineLogger"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PipelineLogger":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._initialized = True
        self._logger: Optional[logging.Logger] = None
        self._handler: Optional[logging.Handler] = None
        self._setup()

    def _setup(self) -> None:
        """Initialize the logger with JSON formatting and file output."""
        config = get_config()
        
        # Ensure logs directory exists
        logs_dir = Path(config["paths"]["logs"])
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        self._logger = logging.getLogger("pipeline")
        self._logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers if setup is called multiple times
        if not self._logger.handlers:
            # File handler for JSON logs
            log_file = logs_dir / "pipeline.jsonl"
            self._handler = logging.FileHandler(log_file, mode='a')
            self._handler.setFormatter(JsonFormatter())
            self._logger.addHandler(self._handler)

            # Also log to stderr for visibility during execution
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(JsonFormatter())
            self._logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        """Return the configured logger instance."""
        if self._logger is None:
            self._setup()
        return self._logger

    def log_event(self, event_name: str, **kwargs: Any) -> None:
        """
        Log a structured event with additional context.

        Args:
            event_name: The name/type of the event.
            **kwargs: Additional key-value pairs to include in the log.
        """
        logger = self.get_logger()
        
        extra_fields = {"event": event_name, **kwargs}
        
        # Create a log record with extra fields
        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            "",
            0,
            f"Event: {event_name}",
            (),
            None
        )
        record.extra_fields = extra_fields
        
        logger.handle(record)

    def log_error(self, message: str, **kwargs: Any) -> None:
        """Log an error with optional context."""
        logger = self.get_logger()
        extra_fields = {"event": "error", **kwargs}
        
        record = logger.makeRecord(
            logger.name,
            logging.ERROR,
            "",
            0,
            message,
            (),
            None
        )
        record.extra_fields = extra_fields
        logger.handle(record)

    def log_progress(self, stage: str, progress: float, total: float, **kwargs: Any) -> None:
        """Log pipeline progress."""
        logger = self.get_logger()
        extra_fields = {
            "event": "progress",
            "stage": stage,
            "progress": progress,
            "total": total,
            "percent": (progress / total * 100) if total > 0 else 0,
            **kwargs
        }
        
        record = logger.makeRecord(
            logger.name,
            logging.INFO,
            "",
            0,
            f"Progress: {stage}",
            (),
            None
        )
        record.extra_fields = extra_fields
        logger.handle(record)


def get_logger() -> logging.Logger:
    """Convenience function to get the pipeline logger."""
    return PipelineLogger().get_logger()


def log_event(event_name: str, **kwargs: Any) -> None:
    """Convenience function to log a structured event."""
    PipelineLogger().log_event(event_name, **kwargs)


def log_error(message: str, **kwargs: Any) -> None:
    """Convenience function to log an error."""
    PipelineLogger().log_error(message, **kwargs)


def log_progress(stage: str, progress: float, total: float, **kwargs: Any) -> None:
    """Convenience function to log pipeline progress."""
    PipelineLogger().log_progress(stage, progress, total, **kwargs)
