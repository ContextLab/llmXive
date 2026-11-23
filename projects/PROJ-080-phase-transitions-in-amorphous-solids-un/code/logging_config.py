"""
Logging infrastructure for the Phase Transitions in Amorphous Solids pipeline.

Configures file handlers to capture warnings, specifically for indeterminate
trajectories and other critical research events.
"""
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Constants
LOG_DIR = Path("logs")
LOG_FILE_NAME = "pipeline.log"
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance
_logger: Optional[logging.Logger] = None


def configure_logging(log_dir: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger with a file handler and console handler.
    
    Args:
        log_dir: Directory to store log files. Defaults to 'logs'.
        log_file: Name of the log file. Defaults to 'pipeline.log'.
    
    Returns:
        The configured logger instance.
    """
    global _logger
    
    if log_dir is None:
        log_dir = str(LOG_DIR)
    if log_file is None:
        log_file = LOG_FILE_NAME
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    full_log_path = log_path / log_file
    
    # Create logger
    _logger = logging.getLogger("llmXive.pipeline")
    _logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Clear existing handlers to avoid duplicates on re-configuration
    if _logger.handlers:
        _logger.handlers.clear()
    
    # Create file handler
    file_handler = logging.FileHandler(full_log_path)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # Create console handler for errors and above (optional, for immediate feedback)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(DEFAULT_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    _logger.addHandler(file_handler)
    _logger.addHandler(console_handler)
    
    return _logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the configured logger or a child logger.
    
    Args:
        name: Optional name for a child logger (e.g., 'preprocess', 'analysis').
    
    Returns:
        A configured logger instance.
    """
    global _logger
    if _logger is None:
        _logger = configure_logging()
    
    if name is None:
        return _logger
    return _logger.getChild(name)


def log_indeterminate_warning(traj_id: str, reason: str) -> None:
    """
    Log a warning for an indeterminate trajectory.
    
    This is the specific function required by T004 to capture warnings
    for indeterminate trajectories as per US1 requirements.
    
    Args:
        traj_id: Identifier for the trajectory being analyzed.
        reason: Explanation of why the trajectory is indeterminate.
    """
    logger = get_logger("preprocess")
    msg = f"INDETERMINATE TRAJECTORY: ID={traj_id}, Reason={reason}"
    logger.warning(msg)


def log_multi_yield_event(traj_id: str, yield_indices: list) -> None:
    """
    Log a warning when multiple yield events are detected in a trajectory.
    
    Args:
        traj_id: Identifier for the trajectory.
        yield_indices: List of timesteps where yield events were detected.
    """
    logger = get_logger("preprocess")
    msg = f"MULTIPLE YIELD EVENTS: ID={traj_id}, Indices={yield_indices}"
    logger.warning(msg)


def log_data_fetch_failure(source: str, error_msg: str) -> None:
    """
    Log an error when real data fetching fails.
    
    Args:
        source: The data source URL or identifier.
        error_msg: The specific error message.
    """
    logger = get_logger("data_loader")
    msg = f"DATA FETCH FAILURE: Source={source}, Error={error_msg}"
    logger.error(msg)


def log_synthetic_fallback_active() -> None:
    """
    Log a critical warning when the pipeline falls back to synthetic data.
    
    This ensures that synthetic fallback is explicitly recorded in the logs
    for auditability, as required by the "fail loud" policy.
    """
    logger = get_logger("data_loader")
    msg = "SYNTHETIC FALLBACK ACTIVE: Real data source unavailable."
    logger.warning(msg)
