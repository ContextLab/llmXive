"""
Logging infrastructure for the project.
Implements T006.
"""
import logging
import os
from pathlib import Path
from typing import Optional, Union

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_level: int = logging.INFO

def get_module_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    Ensures the root logger is configured.

    Args:
        name: The name of the module (usually __name__).

    Returns:
        A configured Logger instance.
    """
    global _logger
    if _logger is None:
        _setup_root_logger()

    return logging.getLogger(name)

def _setup_root_logger() -> None:
    """
    Configure the root logger with a standard handler and format.
    """
    global _logger
    if _logger is not None:
        return

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(_log_level)

    # Clear existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(_log_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_dir / "pipeline.log")
    file_handler.setLevel(_log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    _logger = root_logger

def set_log_level(level: Union[str, int]) -> None:
    """
    Set the global log level.

    Args:
        level: Log level as string (e.g., 'DEBUG') or int.
    """
    global _log_level
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    _log_level = level

    # Update existing handlers if logger is already set
    if _logger:
        for handler in _logger.handlers:
            handler.setLevel(_log_level)

def reset_logger() -> None:
    """
    Reset the logger configuration. Useful for testing.
    """
    global _logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.NOTSET)
    _logger = None
