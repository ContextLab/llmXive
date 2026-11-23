"""
Structured JSON logging for experiment runs.

This module provides a consistent logging configuration that outputs
JSON-formatted log records suitable for automated parsing and analysis.
"""

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .versioning import get_latest_state

# Constants
LOG_LEVEL_ENV = "LLMXIVE_LOG_LEVEL"
DEFAULT_LOG_LEVEL = logging.INFO
LOG_DIR = Path("data/logs")
LOG_FORMATTER = logging.Formatter(
    fmt="%(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)

# Global logger instance (initialized on first use)
_experiment_logger: Optional[logging.Logger] = None
_initialized: bool = False


def _ensure_log_dir() -> Path:
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return LOG_DIR


def _get_log_level() -> int:
    """Get log level from environment or default."""
    level_str = os.environ.get(LOG_LEVEL_ENV, "").upper()
    if not level_str:
        return DEFAULT_LOG_LEVEL
    
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.CRITICAL,
    }
    return level_map.get(level_str, DEFAULT_LOG_LEVEL)


def _create_json_formatter() -> logging.Formatter:
    """Create a formatter that outputs JSON-serializable records."""
    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry: Dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }

            # Add standard attributes if present
            if hasattr(record, "pathname"):
                log_entry["filename"] = os.path.basename(record.pathname)
            if hasattr(record, "lineno"):
                log_entry["line"] = record.lineno
            if hasattr(record, "funcName"):
                log_entry["function"] = record.funcName

            # Add extra fields if present
            if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
                log_entry.update(record.extra_data)

            # Add experiment state if available
            if hasattr(record, "include_state") and record.include_state:
                try:
                    state = get_latest_state()
                    if state:
                        log_entry["experiment_state"] = state
                except Exception:
                    # Silently ignore state retrieval errors to avoid breaking logging
                    pass

            return json.dumps(log_entry)

    return JsonFormatter()


def get_experiment_logger(name: str = "llmxive") -> logging.Logger:
    """
    Get or create the experiment logger with JSON formatting.

    Args:
        name: Logger name (default: "llmxive")

    Returns:
        Configured logger instance
    """
    global _experiment_logger, _initialized

    if _initialized and _experiment_logger is not None:
        return _experiment_logger

    logger = logging.getLogger(name)
    logger.setLevel(_get_log_level())
    logger.handlers = []  # Clear existing handlers

    # Console handler (JSON)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(_get_log_level())
    console_handler.setFormatter(_create_json_formatter())
    logger.addHandler(console_handler)

    # File handler (JSON)
    log_dir = _ensure_log_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"experiment_{timestamp}.jsonl"
    
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(_get_log_level())
    file_handler.setFormatter(_create_json_formatter())
    logger.addHandler(file_handler)

    _experiment_logger = logger
    _initialized = True

    return logger


def log_experiment_start(experiment_name: str, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of an experiment run.

    Args:
        experiment_name: Name of the experiment
        config: Optional configuration dictionary to log
    """
    logger = get_experiment_logger()
    extra = {"experiment_name": experiment_name, "event": "start"}
    if config:
        extra["config"] = config
    
    logger.info(f"Experiment '{experiment_name}' started", extra={"extra_data": extra})


def log_experiment_end(experiment_name: str, success: bool = True, metrics: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the end of an experiment run.

    Args:
        experiment_name: Name of the experiment
        success: Whether the experiment completed successfully
        metrics: Optional metrics dictionary to log
    """
    logger = get_experiment_logger()
    extra = {"experiment_name": experiment_name, "event": "end", "success": success}
    if metrics:
        extra["metrics"] = metrics
    
    logger.info(f"Experiment '{experiment_name}' completed", extra={"extra_data": extra})


def log_metric(name: str, value: Union[int, float, str], tags: Optional[Dict[str, str]] = None) -> None:
    """
    Log a metric value.

    Args:
        name: Metric name
        value: Metric value
        tags: Optional tags for categorization
    """
    logger = get_experiment_logger()
    extra = {"event": "metric", "metric_name": name, "metric_value": value}
    if tags:
        extra["tags"] = tags
    
    logger.info(f"Metric: {name} = {value}", extra={"extra_data": extra})


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error with optional context.

    Args:
        error: The exception that occurred
        context: Optional context dictionary
    """
    logger = get_experiment_logger()
    extra = {"event": "error", "error_type": type(error).__name__, "error_message": str(error)}
    if context:
        extra["context"] = context
    
    logger.error(f"Error occurred: {type(error).__name__}: {str(error)}", extra={"extra_data": extra})


def log_debug(message: str, **kwargs) -> None:
    """Log a debug message with optional extra data."""
    logger = get_experiment_logger()
    extra = {"extra_data": kwargs} if kwargs else {}
    logger.debug(message, extra=extra)


def log_info(message: str, **kwargs) -> None:
    """Log an info message with optional extra data."""
    logger = get_experiment_logger()
    extra = {"extra_data": kwargs} if kwargs else {}
    logger.info(message, extra=extra)


def log_warning(message: str, **kwargs) -> None:
    """Log a warning message with optional extra data."""
    logger = get_experiment_logger()
    extra = {"extra_data": kwargs} if kwargs else {}
    logger.warning(message, extra=extra)


def log_error_message(message: str, **kwargs) -> None:
    """Log an error message with optional extra data."""
    logger = get_experiment_logger()
    extra = {"extra_data": kwargs} if kwargs else {}
    logger.error(message, extra=extra)
