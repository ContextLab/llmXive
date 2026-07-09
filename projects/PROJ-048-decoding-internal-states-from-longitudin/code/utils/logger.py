"""
Structured logging utilities for the llmXive pipeline.

Provides a configured logger that outputs JSON-formatted logs for
easy parsing and monitoring of pipeline stages.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

# Singleton instance to ensure consistent configuration across the pipeline
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.StreamHandler] = None


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Attach exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance with JSON formatting.

    Args:
        name: The name of the logger (default: "llmXive").

    Returns:
        A configured logging.Logger instance.
    """
    global _logger, _handler

    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)

        if not _logger.handlers:
            _handler = logging.StreamHandler(sys.stdout)
            _handler.setFormatter(JSONFormatter())
            _logger.addHandler(_handler)

    return _logger


def log_stage_start(stage: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs the start of a pipeline stage.

    Args:
        stage: The name of the pipeline stage (e.g., "download", "preprocess").
        details: Optional dictionary of metadata for the stage start.
    """
    logger = get_logger()
    extra = {"extra_data": {"stage": stage, "event": "start"} | (details or {})}
    logger.info(f"Stage '{stage}' started", extra=extra)


def log_stage_end(
    stage: str, success: bool = True, details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs the completion of a pipeline stage.

    Args:
        stage: The name of the pipeline stage.
        success: Whether the stage completed successfully.
        details: Optional dictionary of metadata (e.g., duration, output stats).
    """
    logger = get_logger()
    extra = {"extra_data": {"stage": stage, "event": "end", "success": success} | (details or {})}
    level = logging.INFO if success else logging.ERROR
    message = f"Stage '{stage}' completed successfully" if success else f"Stage '{stage}' failed"
    logger.log(level, message, extra=extra)


def log_memory_usage(stage: str, usage_gb: float, limit_gb: float) -> None:
    """
    Logs current memory usage for a specific stage.

    Args:
        stage: The current pipeline stage.
        usage_gb: Current memory usage in GB.
        limit_gb: Configured memory limit in GB.
    """
    logger = get_logger()
    extra = {
        "extra_data": {
            "stage": stage,
            "event": "memory_check",
            "usage_gb": usage_gb,
            "limit_gb": limit_gb,
            "ratio": usage_gb / limit_gb if limit_gb > 0 else float("inf"),
        }
    }
    logger.info(f"Memory usage: {usage_gb:.2f}GB / {limit_gb:.2f}GB", extra=extra)


def log_error(stage: str, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs an error occurring during a pipeline stage.

    Args:
        stage: The pipeline stage where the error occurred.
        error: The exception that was raised.
        details: Optional additional context.
    """
    logger = get_logger()
    extra = {"extra_data": {"stage": stage, "event": "error", "error_type": type(error).__name__} | (details or {})}
    logger.error(f"Error in stage '{stage}': {str(error)}", exc_info=True, extra=extra)