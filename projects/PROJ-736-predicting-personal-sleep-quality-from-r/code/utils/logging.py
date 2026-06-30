"""
Structured JSON logging utilities for the sleep quality prediction pipeline.
Implements FR-010: Structured JSON logging for pipeline stages.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_paths, ensure_dirs


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON lines."""

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

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True,
) -> logging.Logger:
    """
    Configure structured JSON logging for the pipeline.

    Args:
        log_file: Path to the JSON log file. If None, logs only to console.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        console_output: If True, also output logs to stderr.

    Returns:
        Configured logger instance.
    """
    # Get project paths and ensure directories exist
    paths = get_paths()
    log_dir = paths.get("log_dir", "data/logs")
    ensure_dirs([log_dir])

    # Default log file path if not provided
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"pipeline_run_{timestamp}.json")

    # Create logger
    logger = logging.getLogger("sleep_pipeline")
    logger.setLevel(level)
    logger.handlers.clear()  # Clear existing handlers

    # JSON File Handler
    file_handler = logging.FileHandler(log_file, mode="w")
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Console Handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)

    return logger


def log_event(
    logger: logging.Logger,
    message: str,
    level: str = "INFO",
    data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an event with structured data.

    Args:
        logger: The logger instance to use.
        message: The log message.
        level: Log level as string ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        data: Optional dictionary of structured data to include in the log.
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    log_level = level_map.get(level.upper(), logging.INFO)

    # Create a log record with extra data
    extra = {"extra_data": data} if data else {}
    logger.log(log_level, message, extra=extra)


def log_stage_start(
    logger: logging.Logger,
    stage_name: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> None:
    """Log the start of a pipeline stage."""
    log_event(
        logger,
        f"Stage '{stage_name}' started",
        level="INFO",
        data={"stage": stage_name, "parameters": parameters or {}},
    )


def log_stage_complete(
    logger: logging.Logger,
    stage_name: str,
    metrics: Optional[Dict[str, Any]] = None,
) -> None:
    """Log the completion of a pipeline stage."""
    log_event(
        logger,
        f"Stage '{stage_name}' completed",
        level="INFO",
        data={"stage": stage_name, "metrics": metrics or {}},
    )


def log_stage_error(
    logger: logging.Logger,
    stage_name: str,
    error: Exception,
) -> None:
    """Log an error during a pipeline stage."""
    log_event(
        logger,
        f"Stage '{stage_name}' failed with error: {str(error)}",
        level="ERROR",
        data={"stage": stage_name, "error_type": type(error).__name__},
    )


# Example usage and self-test when run directly
if __name__ == "__main__":
    # Initialize logging
    logger = setup_logging(console_output=True)

    # Log a stage start
    log_stage_start(logger, "data_download", {"source": "HCP_1200"})

    # Log a generic event with data
    log_event(
        logger,
        "Processing subject batch",
        level="INFO",
        data={"batch_id": 1, "subject_count": 100},
    )

    # Log a warning
    log_event(
        logger,
        "Low memory warning",
        level="WARNING",
        data={"available_gb": 4.2, "threshold_gb": 5.0},
    )

    # Log stage completion
    log_stage_complete(
        logger,
        "feature_engineering",
        metrics={"features_extracted": 5000, "subjects_processed": 100},
    )

    print("Logging module self-test completed. Check data/logs/ for JSON output.")
