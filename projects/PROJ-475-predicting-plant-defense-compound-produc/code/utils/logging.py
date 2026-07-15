"""
Logging utilities for the Plant Defense Compound Prediction Pipeline.

This module provides centralized logging configuration and logger retrieval.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Union

# Global logger configuration flag
_root_configured = False

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__). If None, returns root logger.
        
    Returns:
        Logger instance
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)

def configure_root_logger(
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    format_str: Optional[str] = None
):
    """
    Configure the root logger with standard formatting.
    
    Args:
        level: Logging level
        log_file: Optional path to log file
        format_str: Optional custom format string
    """
    global _root_configured
    
    if _root_configured:
        return
    
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Default format
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_str)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    _root_configured = True

def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for a specific module.
    
    Args:
        module_name: Module name (usually __name__)
        
    Returns:
        Logger instance configured for the module
    """
    logger = logging.getLogger(module_name)
    if not logger.handlers:
        # Ensure root logger is configured
        if not _root_configured:
            configure_root_logger()
    return logger
