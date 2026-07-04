"""
Logging infrastructure for the llmXive statistical analysis pipeline.

This module provides a centralized logging configuration that ensures:
1. Consistent log formatting across all project modules.
2. Dual output to both console (stdout) and file (logs/project.log).
3. Environment-aware log levels (DEBUG for development, INFO/WARNING for production).
4. Integration with the project's configuration utility (config.py).
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Import project configuration utilities
from src.utils.config import get_project_root, get_config_value

# Default log file path relative to project root
_DEFAULT_LOG_FILENAME = "logs/pipeline.log"
_DEFAULT_LOG_LEVEL = "INFO"
_DEBUG_LOG_LEVEL = "DEBUG"

# Global logger instance
_logger: Optional[logging.Logger] = None


def _get_log_level() -> str:
    """
    Determine the appropriate log level based on environment variables
    or project configuration.

    Priority:
    1. LOG_LEVEL environment variable
    2. config.py setting if available
    3. Default to DEBUG if in a development environment, else INFO
    """
    # Check environment variable first
    env_level = os.environ.get("LOG_LEVEL")
    if env_level:
        return env_level.upper()

    # Check if we are in a debug/development mode
    debug_mode = os.environ.get("DEBUG", "false").lower() == "true"
    if debug_mode:
        return _DEBUG_LOG_LEVEL

    # Default to INFO for production-like environments
    return _DEFAULT_LOG_LEVEL


def _create_log_directory(log_path: Path) -> None:
    """Ensure the directory for the log file exists."""
    log_dir = log_path.parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)


def setup_logging(
    name: str = "llmXive_pipeline",
    log_file: Optional[str] = None,
    level: Optional[str] = None,
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """
    Configure and return a logger instance with standardized formatting.

    Args:
        name: The name of the logger (usually __name__ of the calling module).
        log_file: Optional custom path for the log file. Defaults to logs/pipeline.log.
        level: Optional log level override. Defaults to environment/config or INFO.
        console: If True, add a console handler.
        file: If True, add a file handler.

    Returns:
        A configured logging.Logger instance.
    """
    global _logger

    # If logger already exists and is configured, return it
    if _logger is not None and _logger.hasHandlers():
        return logging.getLogger(name)

    # Resolve log level
    log_level = level if level else _get_log_level()
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Resolve log file path
    project_root = get_project_root()
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = project_root / log_file
    else:
        log_path = project_root / _DEFAULT_LOG_FILENAME

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # Prevent adding handlers multiple times if this function is called repeatedly
    if logger.hasHandlers():
        logger.handlers.clear()

    # Define formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(numeric_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # File Handler
    if file:
        _create_log_directory(log_path)
        fh = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        fh.setLevel(numeric_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Set global reference
    _logger = logger

    return logger


def get_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """
    Retrieve a logger instance. If the logging infrastructure has not been
    explicitly set up via `setup_logging()`, this function will perform
    a lazy initialization with default settings.

    Args:
        name: The name of the logger.

    Returns:
        A configured logging.Logger instance.
    """
    global _logger

    if _logger is None or not _logger.hasHandlers():
        # Lazy initialization
        setup_logging(name=name)

    return logging.getLogger(name)


# Convenience function to ensure logging is initialized early in the pipeline
def init_logging() -> logging.Logger:
    """
    Initialize the logging infrastructure with default settings.
    This is typically called in the main entry point of the application.

    Returns:
        The root logger instance.
    """
    return setup_logging(name="llmXive_pipeline")
