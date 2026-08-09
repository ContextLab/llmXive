"""
Logging configuration for the Solder Hardness Prediction Pipeline.

This module provides centralized logging setup to ensure consistent
log formatting, levels, and output destinations across the entire pipeline.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional

from config import get_log_level, get_log_format


# Global logger instance
_logger: Optional[logging.Logger] = None


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   If None, reads from config.
        log_format: Log format string. If None, reads from config.
        log_file: Optional file path to append logs. If None, logs to console only.
        project_root: Optional project root path for relative file paths.
    
    Returns:
        The configured root logger.
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # Determine log level
    level_str = log_level or get_log_level()
    try:
        level = getattr(logging, level_str.upper(), logging.INFO)
    except AttributeError:
        level = logging.INFO
    
    # Determine format
    fmt_str = log_format or get_log_format()
    formatter = logging.Formatter(fmt_str)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        if project_root:
            log_path = project_root / log_file
        else:
            log_path = Path(log_file)
        
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    _logger = root_logger
    return root_logger


def get_logger(name: str = "solder_pipeline") -> logging.Logger:
    """
    Get a named logger configured with the global settings.
    
    Args:
        name: Logger name (usually __name__ of the calling module).
    
    Returns:
        Configured logger instance.
    """
    if _logger is None:
        # Auto-initialize if not explicitly set up
        setup_logging()
    
    return logging.getLogger(name)
