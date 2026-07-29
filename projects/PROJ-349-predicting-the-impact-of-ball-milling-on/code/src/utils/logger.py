"""
Logging utility for the llmXive research pipeline.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union

_logger: Optional[logging.Logger] = None

def get_logger() -> logging.Logger:
    """
    Get the global logger instance. Initializes it if not already done.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(logging.INFO)

        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)

        # Add handler to logger
        if not _logger.handlers:
            _logger.addHandler(ch)

    return _logger

def get_module_logger(name: str) -> logging.Logger:
    """
    Get a module-specific logger.

    Args:
        name: The name of the module (usually __name__).

    Returns:
        A logger instance for the module.
    """
    parent_logger = get_logger()
    return parent_logger.getChild(name)

def set_log_level(level: Union[str, int]) -> None:
    """
    Set the logging level for the global logger.

    Args:
        level: Logging level (e.g., 'DEBUG', 'INFO', logging.DEBUG).
    """
    logger = get_logger()
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

def reset_logger() -> None:
    """
    Reset the global logger to its initial state.
    """
    global _logger
    if _logger is not None:
        _logger.handlers.clear()
        _logger.setLevel(logging.NOTSET)
        _logger = None
