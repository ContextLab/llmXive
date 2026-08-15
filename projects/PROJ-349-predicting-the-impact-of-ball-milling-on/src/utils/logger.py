"""
Logging utility module.
Provides a consistent logging interface across the project.
"""
import logging
import os
from pathlib import Path
from typing import Optional, Union

# Singleton logger instance
_logger: Optional[logging.Logger] = None

def get_module_logger(name: str) -> logging.Logger:
    """
    Returns a logger for the specified module name.
    If the root logger is not configured, it configures it.
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(logging.INFO)
        
        # Avoid adding handlers multiple times
        if not _logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
    
    return logging.getLogger(name)

def set_log_level(level: Union[str, int]) -> None:
    """
    Sets the global log level.
    Accepts string ('DEBUG', 'INFO', etc.) or integer level.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger("llmXive")
    
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    _logger.setLevel(level)
    for handler in _logger.handlers:
        handler.setLevel(level)

def reset_logger() -> None:
    """Resets the global logger configuration."""
    global _logger
    _logger = None
    logging.getLogger("llmXive").handlers.clear()
    logging.getLogger("llmXive").setLevel(logging.NOTSET)
