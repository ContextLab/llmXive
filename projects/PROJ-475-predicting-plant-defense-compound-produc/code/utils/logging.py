"""
Logging Utility Module.

Provides centralized logger configuration and retrieval.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Union

_loggers = {}

def get_module_logger(name: str) -> logging.Logger:
    """
    Get a module-specific logger.

    Args:
        name: The name of the module (usually __name__).

    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    _loggers[name] = logger
    return logger

def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger for the application.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    root_logger.setLevel(level)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Alias for get_module_logger.

    Args:
        name: Optional module name. If None, returns root logger.

    Returns:
        Logger instance.
    """
    if name is None:
        return logging.getLogger()
    return get_module_logger(name)
