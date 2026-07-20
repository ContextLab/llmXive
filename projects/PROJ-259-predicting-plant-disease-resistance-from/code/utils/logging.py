"""
Structured logging utilities for the plant disease resistance pipeline.

Provides a consistent logging format for pipeline steps, sample exclusions,
and error contexts to ensure reproducibility and auditability.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict

from config import get_artifacts_path


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    Includes timestamp, level, logger name, message, and optional extra context.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "custom_fields"):
            log_entry.update(record.custom_fields)

        # Add pipeline-specific context if available
        if hasattr(record, "pipeline_step"):
            log_entry["pipeline_step"] = record.pipeline_step
        if hasattr(record, "sample_id"):
            log_entry["sample_id"] = record.sample_id
        if hasattr(record, "reason"):
            log_entry["reason"] = record.reason
        if hasattr(record, "modality"):
            log_entry["modality"] = record.modality

        return json.dumps(log_entry)


def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance with structured JSON output.

    Args:
        name: Logger name (usually __name__ of the module)
        log_level: Minimum log level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(StructuredFormatter())

    # Create file handler in artifacts/logs
    artifacts_path = get_artifacts_path()
    log_file = artifacts_path / "logs" / "pipeline.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(logging.DEBUG)  # Capture all detailed logs in file
    file_handler.setFormatter(StructuredFormatter())

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def log_pipeline_step(
    logger: logging.Logger,
    step_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a pipeline step event (start, progress, completion, failure).

    Args:
        logger: Logger instance to use
        step_name: Name of the pipeline step (e.g., "data_download", "feature_selection")
        status: Status string ("START", "COMPLETE", "FAIL", "SKIP")
        details: Optional dictionary of additional context (duration, counts, etc.)
    """
    extra_fields = {"pipeline_step": step_name}
    if details:
        extra_fields.update(details)

    level = logging.INFO
    if status == "FAIL":
        level = logging.ERROR
    elif status == "START":
        level = logging.INFO
    elif status == "COMPLETE":
        level = logging.INFO
    elif status == "SKIP":
        level = logging.WARNING

    logger.log(level, f"Pipeline step: {step_name} - {status}", extra={"custom_fields": extra_fields})


def log_sample_exclusion(
    logger: logging.Logger,
    sample_id: str,
    reason: str,
    modality: Optional[str] = None,
    step_name: Optional[str] = None
) -> None:
    """
    Log a sample exclusion event with structured details.

    This is critical for FR-001 compliance to track why samples are dropped.

    Args:
        logger: Logger instance to use
        sample_id: The ID of the excluded sample
        reason: Reason for exclusion (e.g., "Missing metabolomics data", "ID mismatch")
        modality: Which modality was missing or problematic (optional)
        step_name: Pipeline step where exclusion occurred (optional)
    """
    extra_fields = {
        "sample_id": sample_id,
        "reason": reason,
    }
    if modality:
        extra_fields["modality"] = modality
    if step_name:
        extra_fields["pipeline_step"] = step_name

    logger.warning(
        f"Sample excluded: {sample_id} - Reason: {reason}",
        extra={"custom_fields": extra_fields}
    )


def log_error_context(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any],
    step_name: Optional[str] = None
) -> None:
    """
    Log an error with rich contextual information for debugging.

    Args:
        logger: Logger instance to use
        error: The exception that occurred
        context: Dictionary of contextual data (input paths, parameters, counts, etc.)
        step_name: Pipeline step where error occurred (optional)
    """
    extra_fields = {"error_type": type(error).__name__}
    extra_fields.update(context)
    if step_name:
        extra_fields["pipeline_step"] = step_name

    logger.error(
        f"Error in pipeline: {str(error)}",
        exc_info=True,
        extra={"custom_fields": extra_fields}
    )