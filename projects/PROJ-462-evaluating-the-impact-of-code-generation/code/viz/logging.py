"""
Logging infrastructure for visualization and export operations (User Story 3).

This module establishes logging before implementation of visualization and export
features, following the same pattern as code/ingest/logging.py and code/analysis/logging.py.

Provides:
- get_logger: Base logger factory
- get_viz_logger: Logger for visualization operations
- get_export_logger: Logger for export operations
- setup_basic_logging: Configure logging with file and console handlers
- log_operation_start: Log when an operation begins
- log_operation_end: Log when an operation completes
- log_plot_generation: Log plot creation events
- log_export_result: Log export operation results
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
LOG_DIR = Path("data/output/logs")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Cache for loggers to avoid re-creating them
_loggers = {}

def _get_log_file_path(operation_type: str) -> Path:
    """Generate a log file path with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"{operation_type}_{timestamp}.log"

def setup_basic_logging(
    name: str,
    log_file: Optional[Path] = None,
    level: int = DEFAULT_LOG_LEVEL
) -> logging.Logger:
    """
    Configure basic logging with file and console handlers.
    
    Args:
        name: Logger name (e.g., 'viz', 'export')
        log_file: Optional custom log file path. If None, uses default naming.
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers if already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = _get_log_file_path(name)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str, level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Logger instance
    """
    if name not in _loggers:
        _loggers[name] = setup_basic_logging(name, level=level)
    return _loggers[name]

def get_viz_logger(level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Get the visualization-specific logger.
    
    Args:
        level: Logging level
    
    Returns:
        Visualization logger instance
    """
    return get_logger("viz", level)

def get_export_logger(level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Get the export-specific logger.
    
    Args:
        level: Logging level
    
    Returns:
        Export logger instance
    """
    return get_logger("export", level)

def log_operation_start(logger: logging.Logger, operation: str, details: Optional[str] = None) -> None:
    """
    Log the start of an operation.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        details: Optional additional details
    """
    msg = f"Starting operation: {operation}"
    if details:
        msg += f" - {details}"
    logger.info(msg)

def log_operation_end(logger: logging.Logger, operation: str, success: bool = True, details: Optional[str] = None) -> None:
    """
    Log the end of an operation.
    
    Args:
        logger: Logger instance
        operation: Name of the operation
        success: Whether the operation succeeded
        details: Optional additional details
    """
    status = "completed successfully" if success else "failed"
    msg = f"Operation {operation} {status}"
    if details:
        msg += f" - {details}"
    
    if success:
        logger.info(msg)
    else:
        logger.error(msg)

def log_plot_generation(
    logger: logging.Logger,
    plot_type: str,
    output_path: Path,
  stratification_variable: Optional[str] = None,
    interaction_lines: bool = False
) -> None:
    """
    Log the generation of a visualization plot.
    
    Args:
        logger: Logger instance
        plot_type: Type of plot (e.g., 'boxplot', 'interaction_plot')
        output_path: Path where the plot was saved
        stratification_variable: Variable used for stratification
        interaction_lines: Whether interaction lines were included
    """
    details = f"Type: {plot_type}, Output: {output_path}"
    if stratification_variable:
        details += f", Stratified by: {stratification_variable}"
    if interaction_lines:
        details += ", Interaction lines included"
    
    logger.info(f"Plot generated: {details}")

def log_export_result(
    logger: logging.Logger,
    export_type: str,
    output_path: Path,
    file_size_bytes: Optional[int] = None,
    success: bool = True
) -> None:
    """
    Log the result of an export operation.
    
    Args:
        logger: Logger instance
        export_type: Type of export (e.g., 'csv', 'json', 'png')
        output_path: Path where the file was saved
        file_size_bytes: Size of the exported file in bytes
        success: Whether the export succeeded
    """
    msg = f"Export {export_type} {('successful' if success else 'failed')}: {output_path}"
    if file_size_bytes is not None:
        msg += f" (size: {file_size_bytes} bytes)"
    
    if success:
        logger.info(msg)
    else:
        logger.error(msg)

def log_warning(logger: logging.Logger, message: str) -> None:
    """Log a warning message."""
    logger.warning(message)

def log_error(logger: logging.Logger, message: str) -> None:
    """Log an error message."""
    logger.error(message)

def log_debug(logger: logging.Logger, message: str) -> None:
    """Log a debug message."""
    logger.debug(message)