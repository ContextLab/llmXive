import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from config import get_config, Config

_logger_registry: Dict[str, logging.Logger] = {}
_initialized = False

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves or creates a named logger.
    Ensures the logger is initialized with the project's logging configuration
    (level, handlers) if not already done.
    """
    if name not in _logger_registry:
        logger = logging.getLogger(name)
        # Avoid adding duplicate handlers if logger already exists in registry
        # but ensure it has the correct configuration if it's a fresh creation
        if not logger.handlers:
            # Use StreamHandler by default
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            # Default level, will be updated by initialize_logging
            logger.setLevel(logging.INFO)
        _logger_registry[name] = logger
    return _logger_registry[name]

def initialize_logging(level: Optional[str] = None):
    """
    Initializes the logging infrastructure based on configuration.
    Sets the global level for all registered loggers.
    """
    global _initialized
    if _initialized:
        return

    config = get_config()
    # Fallback to INFO if config is missing or key is missing
    log_level = level or config.logging.get("level", "INFO") if config and hasattr(config, 'logging') else "INFO"
    set_log_level(log_level)
    _initialized = True

def set_log_level(level: str):
    """
    Updates the log level for all currently registered loggers.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    for logger in _logger_registry.values():
        logger.setLevel(numeric_level)

def configure_logger(name: str, level: str, file_path: Optional[str] = None):
    """
    Configures a specific logger with a custom level and optional file handler.
    Useful for writing specific logs to files while keeping console logs separate.
    """
    logger = get_logger(name)
    numeric_level = getattr(level.upper(), logging.INFO) if isinstance(level, str) else logging.INFO
    # Correct getattr usage
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)

    if file_path:
        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file handler already exists to avoid duplicates
        has_file_handler = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
        if not has_file_handler:
            handler = logging.FileHandler(file_path)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

def debug(msg: str, logger_name: str = "root"):
    """Convenience wrapper for debug logging."""
    get_logger(logger_name).debug(msg)

def info(msg: str, logger_name: str = "root"):
    """Convenience wrapper for info logging."""
    get_logger(logger_name).info(msg)

def warning(msg: str, logger_name: str = "root"):
    """Convenience wrapper for warning logging."""
    get_logger(logger_name).warning(msg)

def error(msg: str, logger_name: str = "root"):
    """Convenience wrapper for error logging."""
    get_logger(logger_name).error(msg)

def critical(msg: str, logger_name: str = "root"):
    """Convenience wrapper for critical logging."""
    get_logger(logger_name).critical(msg)