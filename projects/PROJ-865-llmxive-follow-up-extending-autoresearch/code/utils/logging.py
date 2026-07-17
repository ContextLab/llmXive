"""
Structured logging configuration for the llmXive pipeline.

Provides a centralized logging setup that outputs structured JSON logs
to both console and file, with configurable levels and stage-specific
context injection.
"""

import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from utils.config import validate_resource_limits


class StageFilter(logging.Filter):
    """Filter to inject stage context into log records."""

    def __init__(self, stage_name: str):
        super().__init__()
        self.stage_name = stage_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.stage = self.stage_name
        record.timestamp = datetime.now(timezone.utc).isoformat()
        return True


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": getattr(record, "timestamp", datetime.now(timezone.utc).isoformat()),
            "level": record.levelname,
            "stage": getattr(record, "stage", "unknown"),
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
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)


def setup_logging(
    stage_name: str,
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None,
) -> logging.Logger:
    """
    Configure structured logging for a pipeline stage.

    Args:
        stage_name: Name of the current pipeline stage (e.g., "data_ingestion", "annotation")
        log_level: Logging level (default: INFO)
        log_file: Optional path to log file. If None, logs only to console.
        project_root: Root directory of the project. Defaults to current working directory.

    Returns:
        Configured logger instance for the stage.

    Example:
        logger = setup_logging("data_ingestion", log_level=logging.DEBUG)
        logger.info("Starting data download", extra={"extra_data": {"source": "huggingface"}})
    """
    if project_root is None:
        project_root = Path.cwd()

    # Create logger
    logger = logging.getLogger(f"llmxive.{stage_name}")
    logger.setLevel(log_level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Clear any existing handlers
    logger.handlers.clear()

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(JsonFormatter())
    console_handler.addFilter(StageFilter(stage_name))

    logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = project_root / log_file

        # Ensure log directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(JsonFormatter())
        file_handler.addFilter(StageFilter(stage_name))

        logger.addHandler(file_handler)

    return logger


def get_logger(stage_name: str) -> logging.Logger:
    """
    Get a logger instance for a specific stage.

    This function retrieves an existing logger or creates a new one
    with default configuration if it doesn't exist.

    Args:
        stage_name: Name of the pipeline stage.

    Returns:
        Logger instance for the stage.
    """
    logger = logging.getLogger(f"llmxive.{stage_name}")
    if not logger.handlers:
        return setup_logging(stage_name)
    return logger


def log_resource_usage(logger: logging.Logger, stage_name: str) -> None:
    """
    Log current resource usage for monitoring purposes.

    Uses the resource limits defined in config.py to log warnings
    if thresholds are approached.

    Args:
        logger: Logger instance to use.
        stage_name: Name of the current stage.
    """
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        logger.info(
            "Resource usage snapshot",
            extra={"extra_data": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_available_gb": memory.available / (1024 ** 3),
            }},
        )

        # Check against configured limits
        max_cpu, max_memory = validate_resource_limits()
        if cpu_percent > max_cpu * 100:
            logger.warning(
                f"CPU usage ({cpu_percent:.1f}%) exceeds limit ({max_cpu * 100:.1f}%)"
            )
        if memory_percent > max_memory * 100:
            logger.warning(
                f"Memory usage ({memory_percent:.1f}%) exceeds limit ({max_memory * 100:.1f}%)"
            )

    except ImportError:
        logger.debug("psutil not available, skipping resource usage logging")
    except Exception as e:
        logger.debug(f"Could not log resource usage: {e}")


def log_stage_start(logger: logging.Logger, stage_name: str, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of a pipeline stage.

    Args:
        logger: Logger instance.
        stage_name: Name of the stage starting.
        config: Optional configuration dictionary to log.
    """
    msg = f"Stage '{stage_name}' starting"
    if config:
        logger.info(msg, extra={"extra_data": config})
    else:
        logger.info(msg)


def log_stage_end(logger: logging.Logger, stage_name: str, success: bool = True, metrics: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the end of a pipeline stage.

    Args:
        logger: Logger instance.
        stage_name: Name of the stage ending.
        success: Whether the stage completed successfully.
        metrics: Optional metrics dictionary to log.
    """
    if success:
        msg = f"Stage '{stage_name}' completed successfully"
        if metrics:
            logger.info(msg, extra={"extra_data": metrics})
        else:
            logger.info(msg)
    else:
        logger.error(f"Stage '{stage_name}' failed")


# Convenience function for quick logging setup in scripts
def get_pipeline_logger(stage_name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a fully configured logger for a pipeline stage.

    This is a convenience function that sets up logging with
    default settings appropriate for pipeline execution.

    Args:
        stage_name: Name of the pipeline stage.
        log_file: Optional relative path for log file output.

    Returns:
        Configured logger instance.
    """
    return setup_logging(
        stage_name=stage_name,
        log_level=logging.INFO,
        log_file=log_file,
    )