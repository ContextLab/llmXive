"""
Logging utility module for the plant defense compound prediction project.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Union

# Global logger instance
_root_logger: Optional[logging.Logger] = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name. If None, returns the root logger.

    Returns:
        Configured logger instance.
    """
    if name is None:
        if _root_logger is None:
            _root_logger = logging.getLogger()
            _root_logger.setLevel(logging.INFO)
            if not _root_logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                _root_logger.addHandler(handler)
        return _root_logger

    return logging.getLogger(name)

def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger with standard formatting.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    global _root_logger
    _root_logger = logging.getLogger()
    _root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if _root_logger.handlers:
        _root_logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    _root_logger.addHandler(console_handler)

def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        module_name: The module name (usually __name__).

    Returns:
        Configured logger instance for the module.
    """
    logger = logging.getLogger(module_name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # Inherit handlers from root if configured
        if _root_logger and _root_logger.handlers:
            for handler in _root_logger.handlers:
                logger.addHandler(handler)
        else:
            # Fallback: add a console handler
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    return logger
