"""
Logging infrastructure for the llmXive automated science pipeline.

Provides timestamped, multi-level logging with error code tracking.
Integrates with loguru for structured output and file rotation.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import Optional, Dict, List
import json
import traceback

# Configuration constants
LOG_DIR = Path("data/logs")
LOG_FILE = "pipeline.log"
ERROR_TRACKER_FILE = "data/logs/error_tracker.json"
DEFAULT_LEVEL = "INFO"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"

# Error code registry
ERROR_CODES: Dict[int, str] = {
    101: "Insufficient replicates (<3)",
    102: "Excessive replicates (>5)",
    201: "Alignment failed",
    202: "Quantification failed",
    301: "Missing phyloP scores",
    401: "Phylogenetic tree loading failed",
    501: "Lifecycle retention check failed"
}

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Remove default loguru handler to avoid duplicates
logger.remove()

# Add console handler
logger.add(
    sys.stderr,
    format=LOG_FORMAT,
    level=DEFAULT_LEVEL,
    colorize=True
)

# Add file handler with rotation
logger.add(
    LOG_DIR / LOG_FILE,
    format=LOG_FORMAT,
    level=DEFAULT_LEVEL,
    rotation="10 MB",
    retention="7 days",
    compression="zip"
)

# Error tracking storage
_error_tracker: List[Dict] = []

def setup_logger(level: str = DEFAULT_LEVEL, log_file: Optional[str] = None) -> None:
    """
    Configure the logger with a specific level and optional custom log file.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional custom log file path
    """
    global LOG_FILE
    if log_file:
        LOG_FILE = log_file
        # Re-add file handler with new file
        logger.add(
            LOG_DIR / LOG_FILE,
            format=LOG_FORMAT,
            level=level,
            rotation="10 MB",
            retention="7 days",
            compression="zip"
        )
    
    # Update global level
    logger.remove()
    logger.add(sys.stderr, format=LOG_FORMAT, level=level, colorize=True)
    logger.add(LOG_DIR / LOG_FILE, format=LOG_FORMAT, level=level, rotation="10 MB", retention="7 days", compression="zip")

def track_error(error_code: int, message: str, exception: Optional[Exception] = None) -> None:
    """
    Track an error with a specific error code for audit trails.
    
    Args:
        error_code: Numeric error code from ERROR_CODES registry
        message: Human-readable error message
        exception: Optional exception object for traceback
    """
    if error_code not in ERROR_CODES:
        logger.warning(f"Unknown error code {error_code} used")
    
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error_code": error_code,
        "error_name": ERROR_CODES.get(error_code, "Unknown"),
        "message": message,
        "traceback": traceback.format_exc() if exception else None
    }
    
    _error_tracker.append(error_entry)
    logger.error(f"[ERR-{error_code:03d}] {message}")
    
    # Persist error tracker immediately
    _save_error_tracker()

def get_tracked_errors() -> List[Dict]:
    """
    Retrieve all tracked errors.
    
    Returns:
        List of error dictionaries with timestamps and details
    """
    return _error_tracker.copy()

def _save_error_tracker() -> None:
    """Persist error tracker to disk."""
    ERROR_TRACKER_FILE_PATH = LOG_DIR / ERROR_TRACKER_FILE
    try:
        with open(ERROR_TRACKER_FILE_PATH, "w") as f:
            json.dump(_error_tracker, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save error tracker: {e}")

def log_error(error_code: int, message: str, *args, **kwargs) -> None:
    """
    Log an error message and track it with the specified error code.
    
    Args:
        error_code: Numeric error code
        message: Log message (supports loguru formatting)
        *args, **kwargs: Additional arguments for loguru
    """
    track_error(error_code, message)
    logger.error(message, *args, **kwargs)

def log_critical(message: str, *args, **kwargs) -> None:
    """
    Log a critical message (system-level failure).
    
    Args:
        message: Log message
        *args, **kwargs: Additional arguments for loguru
    """
    logger.critical(message, *args, **kwargs)
    # Also track as error code 999 (system critical)
    track_error(999, message)

def log_exception(exception: Exception, message: str = "Unhandled exception", error_code: int = 999) -> None:
    """
    Log and track an exception with traceback.
    
    Args:
        exception: Exception object
        message: Context message
        error_code: Optional error code (default 999 for unhandled)
    """
    track_error(error_code, message, exception)
    logger.exception(f"[ERR-{error_code:03d}] {message}")

def log_pipeline_step(step_name: str, status: str, details: Optional[Dict] = None) -> None:
    """
    Log a pipeline step with structured details.
    
    Args:
        step_name: Name of the pipeline step
        status: Step status (STARTED, COMPLETED, FAILED)
        details: Optional dictionary of step-specific details
    """
    log_entry = f"PIPELINE_STEP: {step_name} | {status}"
    if details:
        log_entry += f" | {details}"
    
    if status == "STARTED":
        logger.info(log_entry)
    elif status == "COMPLETED":
        logger.success(log_entry)
    elif status == "FAILED":
        logger.error(log_entry)
    else:
        logger.warning(log_entry)

def get_log_file_path() -> Path:
    """
    Get the full path to the current log file.
    
    Returns:
        Path object pointing to the log file
    """
    return LOG_DIR / LOG_FILE

def get_error_summary() -> str:
    """
    Generate a summary of all tracked errors.
    
    Returns:
        Formatted string summary of errors
    """
    if not _error_tracker:
        return "No errors tracked."
    
    summary = f"Error Summary ({len(_error_tracker)} total):\n"
    for entry in _error_tracker:
        summary += f"  [{entry['error_code']:03d}] {entry['error_name']}: {entry['message']}\n"
    return summary

# Initialize error tracker on module load
_save_error_tracker()

# Export public API
__all__ = [
    "setup_logger",
    "track_error",
    "get_tracked_errors",
    "log_error",
    "log_critical",
    "log_exception",
    "log_pipeline_step",
    "get_log_file_path",
    "get_error_summary",
    "ERROR_CODES",
    "logger"
]
