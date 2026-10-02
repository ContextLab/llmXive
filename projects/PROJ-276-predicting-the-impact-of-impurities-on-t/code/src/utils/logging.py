"""
Standardized logging configuration for the llmXive MgB2 Impurity Impact project.

Provides pre-configured loggers for ingestion, modeling, and visualization modules,
ensuring consistent log formatting, levels, and handlers across the pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict

# Project root directory for relative path logging
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Log format configuration
_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Cache for created loggers to prevent duplicate handlers
_logger_cache: Dict[str, logging.Logger] = {}


def _get_base_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create or retrieve a named logger with standard configuration.

    Args:
        name: The name of the logger (usually __name__ of the caller).
        level: The logging level to set.

    Returns:
        A configured logging.Logger instance.
    """
    if name in _logger_cache:
        return _logger_cache[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if already present (prevents duplicate logs in tests)
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Optional: File handler for persistent logs (disabled by default to avoid clutter,
        # can be enabled by setting LOG_TO_FILE env var or specific logic if needed)
        # For now, we stick to stdout/stderr for pipeline visibility.

    logger.propagate = False  # Prevent double logging if parent loggers exist
    _logger_cache[name] = logger
    return logger


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Generic logger getter.

    Args:
        name: Logger name.
        level: Minimum log level.

    Returns:
        Configured logger.
    """
    return _get_base_logger(name, level)


def get_ingestion_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Retrieve the logger for data ingestion tasks.

    Args:
        level: Minimum log level (default: INFO).

    Returns:
        Logger instance configured for ingestion modules.
    """
    return _get_base_logger("ingestion", level)


def get_modeling_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Retrieve the logger for model training and evaluation tasks.

    Args:
        level: Minimum log level (default: INFO).

    Returns:
        Logger instance configured for modeling modules.
    """
    return _get_base_logger("modeling", level)


def get_visualization_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Retrieve the logger for visualization and plotting tasks.

    Args:
        level: Minimum log level (default: INFO).

    Returns:
        Logger instance configured for visualization modules.
    """
    return _get_base_logger("visualization", level)


def get_project_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Retrieve the root project logger.

    Args:
        level: Minimum log level (default: INFO).

    Returns:
        Logger instance configured for general project use.
    """
    return _get_base_logger("llmXive_mgb2", level)
