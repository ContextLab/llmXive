"""
Logging infrastructure for the Phase Transitions in Amorphous Solids project.

This module configures Python's logging module to capture warnings, specifically
for indeterminate trajectories as required by US1. It sets up file handlers to
persist logs to disk and provides helper functions for specific warning types.
"""
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project root relative to this file (assuming code/ directory)
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None


def configure_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configure the root logger with file and console handlers.
    
    Args:
        level: The logging level (e.g., logging.INFO, logging.WARNING).
        log_file: Path to the log file. Defaults to logs/pipeline.log.
        console: Whether to also log to stdout/stderr.
    
    Returns:
        The configured logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("amorphous_shearing")
    _logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-run
    if _logger.hasHandlers():
        _logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    file_path = log_file or LOG_FILE
    try:
        fh = logging.FileHandler(file_path, mode='a')
        fh.setLevel(level)
        fh.setFormatter(formatter)
        _logger.addHandler(fh)
    except (OSError, PermissionError) as e:
        # Fallback to console if file write fails, but log the error
        print(f"Warning: Could not create log file at {file_path}: {e}. Logging to console only.")
        fh = None

    # Console Handler
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        _logger.addHandler(ch)

    return _logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a child logger or the main logger.
    
    Args:
        name: Optional sub-logger name (e.g., 'preprocess', 'analysis').
    
    Returns:
        A logging.Logger instance.
    """
    if _logger is None:
        configure_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger


def log_indeterminate_warning(
    trajectory_id: str,
    reason: str,
    logger_name: Optional[str] = None
) -> None:
    """
    Log a specific warning for an indeterminate trajectory.
    
    This function is called when a trajectory does not exhibit a clear
    yielding onset (e.g., no sharp stress drop > 5% detected), flagging
    it as 'indeterminate' as per US1 requirements.
    
    Args:
        trajectory_id: Identifier for the trajectory being processed.
        reason: Explanation of why it is indeterminate.
        logger_name: Optional logger name to use.
    """
    log = get_logger(logger_name)
    warning_msg = f"INDETERMINATE TRAJECTORY [{trajectory_id}]: {reason}"
    log.warning(warning_msg)


def log_multi_yield_event(
    trajectory_id: str,
    detected_drops: int,
    logger_name: Optional[str] = None
) -> None:
    """
    Log a warning when multiple stress drops are detected, violating FR-002.
    
    Args:
        trajectory_id: Identifier for the trajectory.
        detected_drops: Number of significant stress drops found.
        logger_name: Optional logger name.
    """
    log = get_logger(logger_name)
    warning_msg = f"MULTI-YIELD DETECTED [{trajectory_id}]: Found {detected_drops} drops. " \
                  f"Only the first is considered per FR-002. Subsequent drops ignored."
    log.warning(warning_msg)


def log_data_fetch_failure(
    source: str,
    error_msg: str,
    logger_name: Optional[str] = None
) -> None:
    """
    Log a critical failure when real data fetching fails.
    
    Args:
        source: The data source attempted (e.g., HuggingFace ID).
        error_msg: The specific error message from the exception.
        logger_name: Optional logger name.
    """
    log = get_logger(logger_name)
    error_msg_full = f"DATA FETCH FAILED [{source}]: {error_msg}"
    log.error(error_msg_full)
    # Also log to console explicitly if console handler exists
    if _logger:
        for handler in _logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.emit(logging.LogRecord(
                    name="amorphous_shearing",
                    level=logging.ERROR,
                    pathname="logging_config.py",
                    lineno=0,
                    msg=error_msg_full,
                    args=(),
                    exc_info=None
                ))