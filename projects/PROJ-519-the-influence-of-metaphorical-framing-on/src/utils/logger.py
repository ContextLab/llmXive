"""
Base logging and error handling utilities.

Provides a centralized logging configuration and a custom exception hierarchy
for the research pipeline.
"""

import logging
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime

# Custom Exception Hierarchy
class ResearchPipelineError(Exception):
    """Base exception for all research pipeline errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.utcnow().isoformat()

class DataLoadingError(ResearchPipelineError):
    """Raised when data loading fails."""
    pass

class ConfigurationError(ResearchPipelineError):
    """Raised when configuration is invalid or missing."""
    pass

class ValidationError(ResearchPipelineError):
    """Raised when data validation fails."""
    pass

class AnalysisError(ResearchPipelineError):
    """Raised when analysis steps fail."""
    pass

# Logger Configuration
_loggers: Dict[str, logging.Logger] = {}

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_console: bool = True
) -> None:
    """
    Configure the root logger for the application.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs only to console.
        enable_console: If True, logs to stdout.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        root_logger.addHandler(console_handler)

    # File Handler
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.

    Args:
        name: The name of the logger (typically __name__ of the module).

    Returns:
        A configured logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Inherit configuration from root if handlers not explicitly added
            # The root logger is configured via setup_logging()
            pass
        _loggers[name] = logger
    return _loggers[name]
