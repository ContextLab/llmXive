"""
Standardized logging utilities for the llmXive automated science pipeline.

This module provides:
- A centralized logger configuration consistent with project standards.
- Motion threshold logging helpers (specifically for fMRI preprocessing QC).
- Structured error handling wrappers.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Project root resolution (relative to this file's location)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Log file path: data/logs/preprocessing.log
_LOG_DIR = _PROJECT_ROOT / "data" / "logs"
_LOG_FILE = _LOG_DIR / "preprocessing.log"

# Ensure log directory exists
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Logging configuration constants
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = logging.INFO

# Global logger instance
_logger: Optional[logging.Logger] = None


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve or create a named logger with project-standard configuration.

    Args:
        name: Logger name (usually __name__ of the calling module).

    Returns:
        Configured logging.Logger instance.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(LOG_LEVEL)

        # Remove existing handlers to avoid duplicates in repeated calls
        if _logger.handlers:
            _logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT))
        _logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(_LOG_FILE)
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT))
        _logger.addHandler(file_handler)

        # Propagate to root only if needed (usually False for isolated tools)
        _logger.propagate = False

    return logging.getLogger(name)


def log_motion_threshold(
    subject_id: str,
    mean_fd: float,
    threshold: float = 0.5,
    excluded: bool = False,
    reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log motion quality control metrics for a specific subject.

    This function records the mean Framewise Displacement (FD) and whether
    the subject was excluded based on the threshold.

    Args:
        subject_id: The subject identifier.
        mean_fd: The calculated mean FD value.
        threshold: The exclusion threshold (default 0.5mm).
        excluded: Whether the subject was excluded.
        reason: Optional specific reason for exclusion.

    Returns:
        A dictionary containing the logged record details.
    """
    log = get_logger("qc.motion")

    record = {
        "subject_id": subject_id,
        "mean_fd": mean_fd,
        "threshold": threshold,
        "excluded": excluded,
        "reason": reason or ("Motion threshold exceeded" if excluded else None)
    }

    if excluded:
        log.warning(
            "Subject %s excluded due to motion: mean FD = %.4f (threshold = %.2f). Reason: %s",
            subject_id, mean_fd, threshold, record["reason"]
        )
    else:
        log.info(
            "Subject %s passed motion QC: mean FD = %.4f (threshold = %.2f)",
            subject_id, mean_fd, threshold
        )

    return record


def log_preprocessing_step(
    subject_id: str,
    step_name: str,
    status: str,
    duration_seconds: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the status of a preprocessing step for a subject.

    Args:
        subject_id: The subject identifier.
        step_name: Name of the preprocessing step (e.g., 'fmriprep', 'extraction').
        status: Status string ('started', 'completed', 'failed', 'skipped').
        duration_seconds: Optional duration of the step in seconds.
        details: Optional dictionary of additional context.
    """
    log = get_logger("preprocessing")

    msg = f"Subject {subject_id}: {step_name} - {status}"
    if duration_seconds is not None:
        msg += f" (duration: {duration_seconds:.2f}s)"
    if details:
        msg += f" | Details: {details}"

    if status == "failed":
        log.error(msg)
    elif status == "completed":
        log.info(msg)
    elif status == "skipped":
        log.warning(msg)
    else:
        log.debug(msg)


class PipelineError(Exception):
    """Base exception for pipeline-specific errors."""
    pass


class DataFetchError(PipelineError):
    """Raised when real data cannot be fetched from the source."""
    pass


class PreprocessingError(PipelineError):
    """Raised when a preprocessing step fails."""
    pass


def handle_pipeline_exception(
    exc: Exception,
    context: str,
    subject_id: Optional[str] = None
) -> None:
    """
    Centralized exception handler for pipeline operations.

    Logs the error with context and re-raises it to ensure failure is loud.

    Args:
        exc: The caught exception.
        context: A string describing the operation that failed.
        subject_id: Optional subject ID if the error is subject-specific.
    """
    log = get_logger("errors")
    subject_info = f" for subject {subject_id}" if subject_id else ""
    msg = f"Pipeline failure{subject_info} during {context}: {str(exc)}"

    if isinstance(exc, DataFetchError):
        log.critical(msg)
    elif isinstance(exc, PreprocessingError):
        log.error(msg)
    else:
        log.exception(msg)

    # Always re-raise to ensure the process fails loudly
    raise exc