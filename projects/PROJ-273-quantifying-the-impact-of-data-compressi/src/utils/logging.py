"""
Structured logging utilities for the llmXive GW Compression pipeline.

Provides a consistent logging configuration and helper functions to log
pipeline steps, data validation events, and error conditions in a structured
format suitable for CI/CD pipelines and log aggregation systems.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional

# Default log level can be overridden via environment variable LOG_LEVEL
DEFAULT_LEVEL = logging.INFO

# Custom log format for structured output
# We use a JSON-like structure for machine parsing if required, or standard
# timestamped text for human readability. Here we implement a standard
# formatter that includes context.
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class StructuredFormatter(logging.Formatter):
    """
    A custom formatter that outputs log records as JSON for structured logging.
    This is useful for cloud logging (CloudWatch, Stackdriver) or log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra context if provided
        if hasattr(record, "extra_data"):
            log_entry["context"] = record.extra_data

        return json.dumps(log_entry)


def setup_logging(
    name: str = "gw_compression",
    level: int = DEFAULT_LEVEL,
    use_json: bool = False,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with the specified settings.

    Args:
        name: The name of the logger (usually __name__ of the module).
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        use_json: If True, output logs as JSON. If False, use standard text format.
        log_file: Optional path to a log file. If provided, logs are written to file.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if setup is called multiple times
    if logger.handlers:
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if use_json:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))

    logger.addHandler(console_handler)

    # File Handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        if use_json:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid double logging
    logger.propagate = False

    return logger


def log_step_start(logger: logging.Logger, step_name: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the beginning of a pipeline step.

    Args:
        logger: The logger instance to use.
        step_name: Name of the pipeline step (e.g., "download_noise", "inject_signal").
        details: Optional dictionary of context (e.g., event_id, parameters).
    """
    extra = {"extra_data": details} if details else {}
    logger.info(f"Starting step: {step_name}", extra=extra)


def log_step_complete(logger: logging.Logger, step_name: str, duration_seconds: float, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the successful completion of a pipeline step.

    Args:
        logger: The logger instance to use.
        step_name: Name of the pipeline step.
        duration_seconds: Time taken to complete the step.
        details: Optional dictionary of context.
    """
    extra = {"extra_data": details} if details else {}
    extra_data = extra.get("extra_data", {})
    extra_data["duration_seconds"] = duration_seconds
    extra["extra_data"] = extra_data

    logger.info(f"Completed step: {step_name}", extra=extra)


def log_step_error(logger: logging.Logger, step_name: str, error: Exception, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error occurring during a pipeline step.

    Args:
        logger: The logger instance to use.
        step_name: Name of the pipeline step.
        error: The exception that was raised.
        details: Optional dictionary of context.
    """
    extra = {"extra_data": details} if details else {}
    logger.error(f"Error in step: {step_name} - {str(error)}", extra=extra, exc_info=True)


def log_validation_result(logger: logging.Logger, check_name: str, passed: bool, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the result of a validation check.

    Args:
        logger: The logger instance to use.
        check_name: Name of the validation check.
        passed: Boolean indicating if the check passed.
        details: Optional dictionary of context.
    """
    level = logging.INFO if passed else logging.WARNING
    status = "PASSED" if passed else "FAILED"
    extra = {"extra_data": details} if details else {}
    logger.log(level, f"Validation Check: {check_name} - {status}", extra=extra)
