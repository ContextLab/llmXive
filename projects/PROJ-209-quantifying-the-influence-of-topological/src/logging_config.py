"""
Structured logging configuration for the llmXive research pipeline.

This module provides a centralized logging setup that ensures consistent
formatting, levels, and output destinations across all workflow steps.
It supports structured JSON logging for machine-parseable logs and
human-readable console output for development.
"""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Union
from pathlib import Path

# Constants for default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_JSON_FORMAT = {
    "timestamp": "ISO8601",
    "level": "levelname",
    "logger": "name",
    "message": "message",
    "module": "module",
    "function": "funcName",
    "line": "lineno"
}

# Global logger instance cache to prevent re-initialization
_loggers: Dict[str, logging.Logger] = {}
_initialized = False


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON for structured processing.
    Useful for CI/CD pipelines and log aggregation systems.
    """

    def __init__(self, include_stack_trace: bool = False):
        super().__init__()
        self.include_stack_trace = include_stack_trace

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if record.exc_info and self.include_stack_trace:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)


def _get_log_dir() -> Path:
    """Determine the log directory path based on project structure."""
    # Assume standard project root structure: code/../
    # We try to find a 'logs' directory relative to the script or use a default
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    log_dir = project_root / "logs"
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_to_file: bool = True,
    log_to_console: bool = True,
    use_json: bool = False,
    log_dir: Optional[Union[str, Path]] = None,
    logger_name: Optional[str] = None
) -> None:
    """
    Configure the root logger and default handlers.

    Args:
        level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_to_file: Whether to write logs to a file.
        log_to_console: Whether to print logs to stdout/stderr.
        use_json: If True, use JSON formatting; otherwise, use text formatting.
        log_dir: Directory to store log files. Defaults to project_root/logs.
        logger_name: Optional specific logger name to configure. If None, configures root.
    """
    global _initialized

    if _initialized and logger_name is None:
        # Prevent re-configuring the root logger multiple times
        return

    # Determine log directory
    if log_dir is None:
        log_dir = _get_log_dir()
    else:
        log_dir = Path(log_dir)
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)

    # Create logger
    if logger_name:
        logger = logging.getLogger(logger_name)
    else:
        logger = logging.getLogger()
        logger.handlers.clear() # Clear existing handlers to avoid duplicates

    logger.setLevel(level)

    # Formatter selection
    if use_json:
        formatter = StructuredFormatter(include_stack_trace=True)
    else:
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    # Console Handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stdout for h in logger.handlers):
            logger.addHandler(console_handler)

    # File Handler
    if log_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"pipeline_{timestamp}.log"
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) for h in logger.handlers):
            logger.addHandler(file_handler)

    _initialized = True


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve or create a named logger with the configured settings.

    Args:
        name: The name of the logger (usually __name__ of the module).

    Returns:
        A configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    # If root is already configured, this logger inherits handlers
    # If not, we might need to ensure root is configured first
    if not logger.handlers and not logging.root.handlers:
        # Fallback: ensure root is configured if no logger setup happened yet
        setup_logging()

    _loggers[name] = logger
    return logger


def log_workflow_step(
    logger: logging.Logger,
    step_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Helper function to log a structured workflow step event.

    Args:
        logger: The logger instance to use.
        step_name: Name of the workflow step (e.g., "Data Acquisition").
        status: Status of the step (e.g., "STARTED", "COMPLETED", "FAILED").
        details: Optional dictionary of additional context (e.g., file paths, counts).
    """
    extra_data = {
        "workflow_step": step_name,
        "workflow_status": status
    }
    if details:
        extra_data.update(details)

    # Attach extra data to the record
    # We create a custom log record to carry this extra data
    if status == "COMPLETED":
        msg = f"Workflow Step '{step_name}' completed successfully."
        level = logging.INFO
    elif status == "FAILED":
        msg = f"Workflow Step '{step_name}' failed."
        level = logging.ERROR
    elif status == "STARTED":
        msg = f"Workflow Step '{step_name}' started."
        level = logging.INFO
    else:
        msg = f"Workflow Step '{step_name}' status: {status}."
        level = logging.INFO

    logger.log(level, msg, extra={"extra_data": extra_data})


def log_error(
    logger: logging.Logger,
    message: str,
    error: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with optional exception traceback and context.

    Args:
        logger: The logger instance.
        message: The error message.
        error: The exception object to log.
        context: Additional context dictionary.
    """
    extra_data = {"error_type": type(error).__name__ if error else None}
    if context:
        extra_data.update(context)

    logger.error(
        message,
        exc_info=error is not None,
        extra={"extra_data": extra_data}
    )


# Initialize root logger on import if not already done (optional, can be called explicitly)
# setup_logging()