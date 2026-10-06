"""
Standardized logging utilities for the MgB2 Impurity Impact project.

Provides configured loggers for ingestion, modeling, and visualization modules,
ensuring consistent log formatting, levels, and file output across the pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict

# Global registry to ensure single logger instance per name
_loggers: Dict[str, logging.Logger] = {}

# Project root path (assumes code/ is the root for this structure)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"

# Default configuration
_DEFAULT_LEVEL = logging.INFO
_FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def _ensure_log_dir() -> Path:
    """Ensure the logs directory exists."""
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    return _LOG_DIR

def _create_formatter() -> logging.Formatter:
    """Create the standard log formatter."""
    return logging.Formatter(_FORMAT_STRING, _DATE_FORMAT)

def _get_base_logger(name: str, level: int = _DEFAULT_LEVEL) -> logging.Logger:
    """
    Create and configure a base logger with file and console handlers.

    Args:
        name: The name of the logger (module name).
        level: The logging level (default: INFO).

    Returns:
        Configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs from root handlers

    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(_create_formatter())
    logger.addHandler(console_handler)

    # File Handler (optional, based on component)
    # We will add specific file handlers in component-specific getters if needed,
    # or add a generic one here if global logging to file is preferred.
    # For now, we stick to console for standard output, but allow file attachment.

    _loggers[name] = logger
    return logger

def get_logger(name: str, level: int = _DEFAULT_LEVEL, log_to_file: bool = False, filename: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with standard configuration.

    Args:
        name: The name of the logger.
        level: The logging level.
        log_to_file: If True, writes logs to a file in the logs directory.
        filename: Specific filename for log output (defaults to {name}.log).

    Returns:
        Configured logging.Logger instance.
    """
    logger = _get_base_logger(name, level)

    if log_to_file:
        # Check if a file handler for this file already exists to prevent duplicates
        log_filename = filename or f"{name.replace('.', '_')}.log"
        log_path = _ensure_log_dir() / log_filename

        # Check existing handlers
        existing_file_handler = False
        for handler in logger.handlers:
            if isinstance(handler, logging.FileHandler):
                if handler.baseFilename == str(log_path):
                    existing_file_handler = True
                    break

        if not existing_file_handler:
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(_create_formatter())
            logger.addHandler(file_handler)

    return logger

def get_ingestion_logger() -> logging.Logger:
    """
    Get the logger for the ingestion module.

    Returns:
        Configured logger for ingestion tasks.
    """
    return get_logger("src.ingestion", log_to_file=True, filename="ingestion.log")

def get_modeling_logger() -> logging.Logger:
    """
    Get the logger for the modeling module.

    Returns:
        Configured logger for modeling tasks.
    """
    return get_logger("src.modeling", log_to_file=True, filename="modeling.log")

def get_visualization_logger() -> logging.Logger:
    """
    Get the logger for the visualization module.

    Returns:
        Configured logger for visualization tasks.
    """
    return get_logger("src.visualization", log_to_file=True, filename="visualization.log")

def get_project_logger() -> logging.Logger:
    """
    Get the generic project logger for high-level or utility logging.

    Returns:
        Configured logger for general project use.
    """
    return get_logger("project_utils", log_to_file=True, filename="project.log")
