"""
Standardized error handling and progress logging for the llmXive SLR pipeline.

This module provides:
- Custom exception classes for different failure modes
- A centralized logger configuration
- Progress logging utilities for long-running tasks
- Error handling wrappers
"""

import logging
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime
import traceback


# --- Custom Exceptions ---

class PipelineError(Exception):
    """Base exception for pipeline-specific errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self):
        base = super().__str__()
        if self.context:
            return f"{base} | Context: {self.context}"
        return base


class DataUnavailableError(PipelineError):
    """Raised when required data is missing or inaccessible."""
    pass


class ConfigurationError(PipelineError):
    """Raised when configuration is invalid or missing required keys."""
    pass


class AnalysisError(PipelineError):
    """Raised when an analysis step fails (e.g., non-convergence, math error)."""
    pass


# --- Logger Configuration ---

_logger_instance: Optional[logging.Logger] = None
_initialized: bool = False


def get_logger(name: str = "slr_pipeline") -> logging.Logger:
    """
    Get or create the centralized logger instance.

    Args:
        name: Logger name (defaults to 'slr_pipeline')

    Returns:
        Configured logging.Logger instance
    """
    global _logger_instance, _initialized

    if _initialized and _logger_instance is not None:
        return _logger_instance

    _logger_instance = logging.getLogger(name)
    
    # Avoid duplicate handlers if called multiple times in same process
    if _logger_instance.handlers:
        _initialized = True
        return _logger_instance

    _logger_instance.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # File handler (optional, if LOG_FILE env var is set)
    log_file = os.getenv("LOG_FILE")
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        _logger_instance.addHandler(file_handler)

    _logger_instance.addHandler(console_handler)
    _initialized = True

    return _logger_instance


# --- Progress Logging ---

def log_progress(
    stage: str,
    message: str,
    current: Optional[int] = None,
    total: Optional[int] = None,
    logger_name: str = "slr_pipeline"
) -> None:
    """
    Log a progress update with optional percentage calculation.

    Args:
        stage: Current stage name (e.g., "Data Ingestion")
        message: Descriptive message
        current: Current item count (optional)
        total: Total item count (optional)
        logger_name: Logger name to use
    """
    logger = get_logger(logger_name)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    progress_str = ""
    if current is not None and total is not None and total > 0:
        pct = (current / total) * 100
        progress_str = f" [{current}/{total} | {pct:.1f}%]"

    log_line = f"[{stage}] {message}{progress_str}"
    logger.info(log_line)


def log_error(
    error: Exception,
    stage: str,
    logger_name: str = "slr_pipeline",
    include_traceback: bool = True
) -> None:
    """
    Log an error with context and optional traceback.

    Args:
        error: The exception instance
        stage: Stage where error occurred
        logger_name: Logger name to use
        include_traceback: Whether to include full traceback
    """
    logger = get_logger(logger_name)
    error_msg = f"[{stage}] ERROR: {type(error).__name__}: {str(error)}"

    if include_traceback:
        tb = traceback.format_exc()
        logger.error(f"{error_msg}\n{tb}")
    else:
        logger.error(error_msg)


def handle_fatal_error(
    error: Exception,
    stage: str,
    logger_name: str = "slr_pipeline",
    exit_code: int = 1
) -> None:
    """
    Log a fatal error and exit the program.

    Args:
        error: The exception instance
        stage: Stage where error occurred
        logger_name: Logger name to use
        exit_code: Exit code for the process
    """
    log_error(error, stage, logger_name, include_traceback=True)
    log_progress(stage, "FATAL ERROR - Pipeline terminating", logger_name=logger_name)
    sys.exit(exit_code)


def init_logging(log_level: str = "INFO") -> None:
    """
    Initialize logging with a specific level.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

    log_progress("System", f"Logging initialized at level {log_level}")