"""
Logging infrastructure for statistical analysis operations.

This module establishes logging before the implementation of statistical
analysis functions (ANOVA, effect sizes, etc.) as required by T030.
"""
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Define log directory
LOG_DIR = Path(__file__).parent.parent.parent / "data" / "output" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger registry to avoid duplicate handlers
_loggers: dict = {}

def _get_log_file_path(module_name: str) -> Path:
    """Generate a timestamped log file path for a specific module."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"{module_name}_{timestamp}.log"

def get_logger(module_name: str = "analysis") -> logging.Logger:
    """
    Get or create a logger for the analysis module.
    
    Args:
        module_name: Name of the module requesting the logger.
        
    Returns:
        Configured logging.Logger instance.
    """
    if module_name in _loggers:
        return _loggers[module_name]

    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding duplicate handlers if logger already exists in hierarchy
    if not logger.handlers:
        # Create file handler
        log_file = _get_log_file_path(module_name)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Create console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        # Log initialization
        logger.info(f"Logger initialized for {module_name}. Log file: {log_file}")

    _loggers[module_name] = logger
    return logger

def get_anova_logger() -> logging.Logger:
    """Get the specific logger for ANOVA operations."""
    return get_logger("analysis.anova")

def get_effect_sizes_logger() -> logging.Logger:
    """Get the specific logger for effect size calculations."""
    return get_logger("analysis.effect_sizes")

def get_sensitivity_logger() -> logging.Logger:
    """Get the specific logger for sensitivity analysis."""
    return get_logger("analysis.sensitivity")

def setup_basic_logging(level: int = logging.INFO) -> None:
    """
    Setup basic logging configuration for the analysis module.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    root_logger = get_logger()
    root_logger.setLevel(level)
    root_logger.info(f"Basic logging setup complete at level: {logging.getLevelName(level)}")

def log_operation_start(operation: str, details: Optional[dict] = None) -> None:
    """
    Log the start of an analysis operation.
    
    Args:
        operation: Name of the operation (e.g., "two_way_anova", "cohens_d").
        details: Optional dictionary of operation parameters.
    """
    logger = get_logger()
    msg = f"Starting operation: {operation}"
    if details:
        msg += f" | Parameters: {details}"
    logger.info(msg)

def log_operation_end(operation: str, success: bool, duration_seconds: Optional[float] = None) -> None:
    """
    Log the completion of an analysis operation.
    
    Args:
        operation: Name of the operation.
        success: Whether the operation completed successfully.
        duration_seconds: Optional duration of the operation.
    """
    logger = get_logger()
    status = "SUCCESS" if success else "FAILED"
    msg = f"Operation completed: {operation} | Status: {status}"
    if duration_seconds is not None:
        msg += f" | Duration: {duration_seconds:.2f}s"
    if success:
        logger.info(msg)
    else:
        logger.error(msg)

def log_analysis_result(operation: str, result_summary: dict) -> None:
    """
    Log the results of a statistical analysis.
    
    Args:
        operation: Name of the operation.
        result_summary: Dictionary containing key result metrics (e.g., p-value, F-stat).
    """
    logger = get_logger()
    logger.info(f"Results for {operation}: {result_summary}")

def log_warning(message: str) -> None:
    """Log a warning message."""
    get_logger().warning(message)

def log_error(message: str) -> None:
    """Log an error message."""
    get_logger().error(message)

def log_debug(message: str) -> None:
    """Log a debug message."""
    get_logger().debug(message)