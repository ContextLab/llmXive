"""
Logging configuration and utilities for the HEA Elastic Modulus project.

This module provides a centralized logging setup to ensure consistent
logging across all project components. It supports:
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File and console output
- Timestamped log entries
- Thread-safe logging operations
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime


# Global state to track initialization
_logging_initialized: bool = False
_current_config: Dict = {}
_logger_instance: Optional[logging.Logger] = None


def get_log_level(level_str: str) -> int:
    """
    Convert a string log level to the corresponding logging constant.

    Args:
        level_str: String representation of log level (e.g., 'DEBUG', 'INFO')

    Returns:
        The corresponding logging level constant

    Raises:
        ValueError: If the log level string is invalid
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }
    level_upper = level_str.upper()
    if level_upper not in level_map:
        raise ValueError(f"Invalid log level: {level_str}. Must be one of {list(level_map.keys())}")
    return level_map[level_upper]


def setup_logging(
    log_file: Optional[Path] = None,
    level: str = 'INFO',
    console_output: bool = True,
    file_output: bool = True,
    project_root: Optional[Path] = None
) -> Dict:
    """
    Configure the root logger with the specified settings.

    This function sets up both console and file handlers with consistent
    formatting. It should be called once at the start of the application.

    Args:
        log_file: Path to the log file. If None, no file output is created.
        level: Log level as a string (e.g., 'DEBUG', 'INFO')
        console_output: Whether to log to console
        file_output: Whether to log to file
        project_root: Root directory of the project. Used to resolve relative paths.

    Returns:
        Dictionary containing the current configuration
    """
    global _logging_initialized, _current_config, _logger_instance

    # Get the log level
    log_level = get_log_level(level)

    # Determine the log file path
    if log_file:
        if not log_file.is_absolute() and project_root:
            log_file = project_root / log_file
        log_file.parent.mkdir(parents=True, exist_ok=True)
    elif project_root:
        log_file = project_root / "logs" / f"hea_pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler
    if file_output and log_file:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Store configuration
    _current_config = {
        'level': level,
        'log_file': str(log_file) if log_file else None,
        'console_output': console_output,
        'file_output': file_output,
        'handlers_count': len(root_logger.handlers),
        'initialized_at': datetime.now().isoformat()
    }

    _logging_initialized = True
    _logger_instance = root_logger

    return _current_config


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a specific name.

    This function returns the root logger if no name is provided,
    or a child logger with the specified name.

    Args:
        name: Optional name for the logger (e.g., 'src.data.fetch_oqmd')

    Returns:
        A configured logger instance
    """
    if not _logging_initialized:
        # Initialize with defaults if not already set up
        setup_logging(level='INFO')

    if name:
        return logging.getLogger(name)
    return logging.getLogger()


def configure_module_logging(module_name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for a specific module with optional level override.

    Args:
        module_name: The name of the module (e.g., 'src.data.fetch_oqmd')
        level: Optional log level override for this module

    Returns:
        Configured logger for the module
    """
    logger = get_logger(module_name)
    if level:
        logger.setLevel(get_log_level(level))
    else:
        # Inherit from root logger
        logger.setLevel(logging.NOTSET)
    return logger


def is_logging_initialized() -> bool:
    """
    Check if logging has been initialized.

    Returns:
        True if logging is initialized, False otherwise
    """
    return _logging_initialized


def get_current_config() -> Dict:
    """
    Get the current logging configuration.

    Returns:
        Dictionary containing the current configuration
    """
    return _current_config.copy()


# Convenience function to initialize logging with defaults
def init_default_logging(project_root: Optional[Path] = None) -> Dict:
    """
    Initialize logging with default settings.

    This is a convenience function for quick setup with sensible defaults.

    Args:
        project_root: Root directory of the project

    Returns:
        Dictionary containing the current configuration
    """
    return setup_logging(
        level='INFO',
        console_output=True,
        file_output=True,
        project_root=project_root
    )
