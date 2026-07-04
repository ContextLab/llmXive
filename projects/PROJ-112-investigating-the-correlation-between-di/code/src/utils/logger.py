import logging
import os
from pathlib import Path
from typing import Optional
import sys

# Configuration constants
_LOG_DIR = "logs"
_LOG_FILE = "pipeline.log"
_FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_MAASLIN2_FORMAT_STRING = "%(asctime)s - %(name)s - %(levelname)s - [MaAsLin2] %(message)s"

# Global registry to prevent duplicate handlers
_LOGGER_REGISTRY = {}

def _setup_log_directory():
    """Ensure the log directory exists."""
    log_path = Path(_LOG_DIR)
    if not log_path.exists():
        log_path.mkdir(parents=True, exist_ok=True)

def _get_console_handler() -> logging.Handler:
    """Create a console handler with standard formatting."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(_FORMAT_STRING)
    handler.setFormatter(formatter)
    return handler

def _get_file_handler() -> logging.Handler:
    """Create a file handler with standard formatting."""
    _setup_log_directory()
    file_path = Path(_LOG_DIR) / _LOG_FILE
    handler = logging.FileHandler(str(file_path))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(_FORMAT_STRING)
    handler.setFormatter(formatter)
    return handler

def _get_maaslin2_handler() -> logging.Handler:
    """
    Create a specific handler for MaAsLin2 execution status, 
    convergence warnings, and R-package output capture.
    """
    _setup_log_directory()
    # Separate file for R/MaAsLin2 specific logs to isolate noise
    maaslin2_file = Path(_LOG_DIR) / "maaslin2_execution.log"
    handler = logging.FileHandler(str(maaslin2_file))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(_MAASLIN2_FORMAT_STRING)
    handler.setFormatter(formatter)
    return handler

def get_logger(name: str, force_new: bool = False) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__).
        force_new: If True, forces creation of a new logger even if cached.
    
    Returns:
        Configured logging.Logger instance.
    """
    if name in _LOGGER_REGISTRY and not force_new:
        return _LOGGER_REGISTRY[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent adding handlers multiple times if called repeatedly
    if not logger.handlers or force_new:
        # Clear existing handlers to avoid duplicates if force_new
        logger.handlers.clear()
        
        # Add standard handlers
        logger.addHandler(_get_console_handler())
        logger.addHandler(_get_file_handler())
        
        # Add specialized MaAsLin2 handler
        # This ensures any specific MaAsLin2 logs are captured distinctly
        logger.addHandler(_get_maaslin2_handler())
    
    _LOGGER_REGISTRY[name] = logger
    return logger

def reset_loggers():
    """Reset all loggers and clear the registry (useful for testing)."""
    _LOGGER_REGISTRY.clear()
    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)
