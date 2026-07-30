import logging
import os
from pathlib import Path
from typing import Optional, Union

_logger_instance = None
_log_level = logging.INFO

def get_module_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance for the given module name.
    Ensures the logger is configured with the project's settings.
    """
    global _logger_instance
    if _logger_instance is None:
        _configure_root_logger()
        _logger_instance = logging.getLogger("project_root")
    
    logger = logging.getLogger(name)
    logger.handlers = [] 
    logger.propagate = False
    
    # Add a handler if not already present to ensure it logs
    # In a complex app, we might manage handlers globally, 
    # but here we ensure the specific logger has a stream handler.
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(_log_level)
    
    return logger

def _configure_root_logger():
    global _logger_instance
    if _logger_instance is not None:
        return
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

def set_log_level(level: Union[int, str]):
    global _log_level
    if isinstance(level, str):
        _log_level = getattr(logging, level.upper())
    else:
        _log_level = level
    
    logging.getLogger("project_root").setLevel(_log_level)
    for handler in logging.getLogger("project_root").handlers:
        handler.setLevel(_log_level)

def reset_logger():
    global _logger_instance, _log_level
    _logger_instance = None
    _log_level = logging.INFO
    logging.getLogger().handlers = []
