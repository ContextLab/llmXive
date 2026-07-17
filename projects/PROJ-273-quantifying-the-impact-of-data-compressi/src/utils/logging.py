"""
Structured logging utilities for the GW Compression Impact pipeline.

This module provides a centralized logging configuration that ensures:
- Consistent log formatting across all pipeline stages.
- Structured JSON output for CI/CD integration and log aggregation.
- Level-based filtering (INFO by default, DEBUG for troubleshooting).
- File and console handlers for persistent and immediate visibility.
"""

import logging
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_JSON_FORMAT = "json"
LOG_FILE_NAME = "pipeline.log"
LOG_DIR = Path("logs")

# Global logger instance cache
_configured = False
_logger: Optional[logging.Logger] = None


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines for structured parsing.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: Optional[Path] = None,
    use_json: bool = False,
) -> logging.Logger:
    """
    Configure the root logger and return a named logger for the pipeline.

    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_dir: Directory to store log files. Defaults to 'logs' in project root.
        use_json: If True, output logs in JSON format. If False, use standard text format.

    Returns:
        A configured logger instance named 'gw_compression_pipeline'.

    Raises:
        ValueError: If log_dir is provided but cannot be created.
    """
    global _configured, _logger

    if _configured:
        return _logger

    # Ensure log directory exists
    if log_dir is None:
        log_dir = LOG_DIR
    else:
        log_dir = Path(log_dir)

    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ValueError(f"Failed to create log directory {log_dir}: {e}")

    log_file_path = log_dir / LOG_FILE_NAME

    # Create logger
    logger = logging.getLogger("gw_compression_pipeline")
    logger.setLevel(log_level)
    logger.propagate = False  # Prevent duplicate logs if root is also configured

    # Clear existing handlers to avoid duplication on re-calls
    logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if use_json:
        console_formatter = StructuredFormatter()
    else:
        console_formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(console_formatter)
    logger.addHandler(file_handler)

    _configured = True
    _logger = logger

    logger.info("Logging initialized", extra={"extra_data": {"log_file": str(log_file_path), "level": logging.getLevelName(log_level)}})
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a child logger from the pipeline logger.

    Args:
        name: Optional sub-name for the logger (e.g., "data.download").

    Returns:
        A logger instance.
    """
    if _logger is None:
        # Auto-initialize if not explicitly set up yet
        setup_logging()

    if name:
        return _logger.getChild(name)
    return _logger


def log_step_start(step_name: str, **kwargs) -> None:
    """Log the beginning of a pipeline step."""
    logger = get_logger(step_name)
    logger.info(f"Step '{step_name}' started", extra={"extra_data": {"step": step_name, **kwargs}})


def log_step_success(step_name: str, **kwargs) -> None:
    """Log the successful completion of a pipeline step."""
    logger = get_logger(step_name)
    logger.info(f"Step '{step_name}' completed successfully", extra={"extra_data": {"step": step_name, **kwargs}})


def log_step_failure(step_name: str, error: Exception, **kwargs) -> None:
    """Log the failure of a pipeline step."""
    logger = get_logger(step_name)
    logger.error(f"Step '{step_name}' failed: {str(error)}", extra={"extra_data": {"step": step_name, "error": str(error), **kwargs}}, exc_info=True)
