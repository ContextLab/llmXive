"""
Logging infrastructure for the llmXive pipeline.
Provides structured JSON output for pipeline steps to ensure reproducibility and
machine-parseable logs for downstream analysis.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Includes timestamp, level, logger name, message, and optional extra context.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "run_id": getattr(record, 'run_id', None),
        }

        # Append any extra fields passed in the log call
        if hasattr(record, 'extra_data'):
            log_entry["data"] = record.extra_data

        # Handle exceptions if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_pipeline_logger(
    log_path: Optional[Path] = None,
    run_id: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configures and returns a logger for pipeline execution.

    Args:
        log_path: Directory to write log files. If None, logs only to stdout.
        run_id: Unique identifier for this pipeline run (added to log records).
        level: Logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        A configured logger instance.
    """
    if run_id is None:
        run_id = str(uuid4())

    logger = logging.getLogger("llmXive.pipeline")
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        logger.handlers.clear()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File handler (if path provided)
    if log_path:
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / f"pipeline_{run_id}.log"
        file_handler = logging.FileHandler(log_file, mode='w')
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    # Attach run_id to the logger for propagation to all records
    logger.run_id = run_id

    return logger


def log_step(
    logger: logging.Logger,
    message: str,
    step_name: str,
    status: str = "START",
    data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Logs a structured pipeline step event.

    Args:
        logger: The logger instance.
        message: Human-readable description of the step.
        step_name: Machine-readable name of the step (e.g., "download_data").
        status: One of "START", "SUCCESS", "FAILURE", "SKIP".
        data: Optional dictionary of metrics or context to include.
    """
    extra = {
        "step_name": step_name,
        "status": status,
    }
    if data:
        extra["data"] = data

    # Attach to the record via extra
    logger.info(
        f"[{step_name}] {message} ({status})",
        extra={"extra_data": extra}
    )


def log_error(
    logger: logging.Logger,
    message: str,
    error: Exception,
    step_name: str
) -> None:
    """
    Logs a pipeline failure with exception details.

    Args:
        logger: The logger instance.
        message: Contextual message describing the failure.
        error: The exception instance.
        step_name: The step where the error occurred.
    """
    logger.error(
        f"[{step_name}] {message}",
        exc_info=True,
        extra={"extra_data": {"step_name": step_name, "status": "FAILURE"}}
    )