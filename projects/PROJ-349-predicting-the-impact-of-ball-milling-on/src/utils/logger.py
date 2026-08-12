"""
Logging utilities for the ball milling prediction pipeline.
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
    Get a logger instance for a specific module.

    Args:
        name: Module name (usually __name__).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(_log_level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(_log_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger


def set_log_level(level: Union[int, str]) -> None:
    """
    Set the global log level.

    Args:
        level: Log level as integer or string (e.g., 'DEBUG', 'INFO').
    """
    global _log_level
    
    if isinstance(level, str):
        _log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        _log_level = level
    
    # Update all existing handlers
    for logger in logging.root.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(_log_level)
            for handler in logger.handlers:
                handler.setLevel(_log_level)


def reset_logger() -> None:
    """Reset the logger configuration to defaults."""
    global _logger, _log_level
    _logger = None
    _log_level = logging.INFO
    logging.root.handlers = []
