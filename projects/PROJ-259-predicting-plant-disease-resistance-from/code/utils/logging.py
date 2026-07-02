"""
Structured logging utilities for the plant disease resistance pipeline.

This module provides:
- A configured logger that writes JSON-formatted logs to files and console.
- Helpers to log pipeline steps, sample exclusions, and warnings.
- Integration with the project's exception classes.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import get_path, load_config
from utils.exceptions import PipelineException


class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logger(
    name: str = "pipeline",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return a logger with JSON formatting.

    Args:
        name: Logger name (usually 'pipeline').
        log_file: Relative path from project root to write logs. If None,
                  logs only to console.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(JsonFormatter())
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        # Resolve path relative to project root
        full_path = get_path(log_file)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(full_path, mode="a")
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return logger


def log_pipeline_step(
    logger: logging.Logger,
    step_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log a structured message about a pipeline step.

    Args:
        logger: The logger instance.
        step_name: Name of the pipeline step (e.g., 'preprocess', 'split').
        status: Status of the step (e.g., 'START', 'COMPLETE', 'FAILED').
        details: Optional dictionary of step-specific metrics or metadata.
    """
    extra_data = {"step": step_name, "status": status}
    if details:
        extra_data.update(details)

    # Attach extra_data to the log record
    record = logger.makeRecord(
        logger.name,
        logging.INFO if status == "COMPLETE" else (logging.ERROR if status == "FAILED" else logging.INFO),
        "",
        0,
        f"Pipeline step: {step_name} [{status}]",
        (),
        None,
    )
    record.extra_data = extra_data
    logger.handle(record)


def log_sample_exclusion(
    logger: logging.Logger,
    sample_id: str,
    reason: str,
    modality: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> None:
    """
    Log a structured exclusion event for a sample.

    Args:
        logger: The logger instance.
        sample_id: The ID of the excluded sample.
        reason: Human-readable reason for exclusion.
        modality: The modality involved (e.g., 'SNP', 'metabolite', 'phenotype').
        timestamp: Optional timestamp (defaults to current UTC time).
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat() + "Z"

    extra_data = {
        "sample_id": sample_id,
        "exclusion_reason": reason,
        "modality": modality,
        "timestamp": timestamp,
    }

    record = logger.makeRecord(
        logger.name,
        logging.WARNING,
        "",
        0,
        f"Sample excluded: {sample_id} - {reason}",
        (),
        None,
    )
    record.extra_data = extra_data
    logger.handle(record)


def log_config_summary(logger: logging.Logger, config: Dict[str, Any]) -> None:
    """
    Log a summary of the loaded configuration (excluding secrets).

    Args:
        logger: The logger instance.
        config: The configuration dictionary.
    """
    # Filter out potential secrets (keys containing 'secret', 'password', 'key')
    safe_config = {
        k: v for k, v in config.items()
        if not any(s in k.lower() for s in ["secret", "password", "key", "token"])
    }

    extra_data = {"config_summary": safe_config}
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        "Configuration loaded successfully",
        (),
        None,
    )
    record.extra_data = extra_data
    logger.handle(record)