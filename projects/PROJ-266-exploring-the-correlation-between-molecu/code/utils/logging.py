"""
Standardized logging configuration for llmXive research pipeline.

Provides centralized logger creation, root configuration, and log file path resolution.
Ensures consistent formatting and level settings across all project modules.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from .config import get_project_root


# Default log format with ISO8601 timestamp
_DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

# Cache for configured loggers to prevent duplicate handlers
_logger_cache: dict[str, logging.Logger] = {}


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a named logger with standardized configuration.
    
    Args:
        name: Logger name (typically __name__ of the calling module).
        level: Optional log level override (default: INFO).
    
    Returns:
        Configured logging.Logger instance.
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    if name in _logger_cache:
        return _logger_cache[name]
    
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        logger.setLevel(level if level is not None else logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DATE_FORMAT))
        console_handler.setLevel(logging.DEBUG)
        
        logger.addHandler(console_handler)
        
        # Add file handler if logs directory exists
        log_path = get_log_path()
        if log_path.exists():
            file_handler = logging.FileHandler(
                log_path / f"{name}.log",
                mode='a',
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DATE_FORMAT))
            file_handler.setLevel(logging.DEBUG)
            logger.addHandler(file_handler)
    
    logger.propagate = False
    _logger_cache[name] = logger
    return logger


def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger with standardized settings.
    
    This should be called once at the entry point of any script to ensure
    consistent logging behavior across all modules.
    
    Args:
        level: Minimum log level for the root logger (default: INFO).
    """
    root = logging.getLogger()
    
    # Only configure if not already configured
    if not root.handlers:
        root.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DATE_FORMAT))
        console_handler.setLevel(logging.DEBUG)
        
        root.addHandler(console_handler)
        
        # File handler for root
        log_path = get_log_path()
        if log_path.exists():
            file_handler = logging.FileHandler(
                log_path / "root.log",
                mode='a',
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter(_DEFAULT_FORMAT, _DATE_FORMAT))
            file_handler.setLevel(logging.DEBUG)
            root.addHandler(file_handler)


def get_log_path() -> Path:
    """
    Get the absolute path to the project logs directory.
    
    Returns:
        Path object pointing to the logs directory.
    
    Raises:
        FileNotFoundError: If the logs directory does not exist.
    """
    log_path = get_project_root() / "logs"
    if not log_path.exists():
        log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def setup_logging_for_script(script_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Convenience function to set up logging for a script entry point.
    
    Args:
        script_name: Name of the script (used for logger name and log file).
        level: Log level for the script (default: INFO).
    
    Returns:
        Configured logger instance for the script.
    
    Example:
        >>> if __name__ == "__main__":
        ...     logger = setup_logging_for_script(__name__)
        ...     logger.info("Script starting")
    """
    configure_root_logger(level)
    return get_logger(script_name, level)