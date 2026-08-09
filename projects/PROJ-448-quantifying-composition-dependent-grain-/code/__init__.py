"""
llmXive Research Pipeline - Code Package.

This package provides the core implementation for the 
Quantifying Composition-Dependent Grain Boundary Segregation in BCC Alloys project.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Configure project-wide logging infrastructure
def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure and return the project root logger with consistent formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to write logs to file
        project_root: Optional project root directory for relative paths
        
    Returns:
        Configured root logger instance
        
    Raises:
        ValueError: If log_level is invalid
    """
    # Validate log level
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    log_level_upper = log_level.upper()
    if log_level_upper not in valid_levels:
        raise ValueError(f"Invalid log level '{log_level}'. Must be one of: {valid_levels}")
    
    # Create project root logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, log_level_upper))
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Define formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_file:
        log_path = Path(log_file)
        if project_root and not log_path.is_absolute():
            log_path = Path(project_root) / log_file
        
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize default logger
# Note: This is a placeholder; actual configuration happens in config.py
_default_logger = None

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance, creating it if necessary.
    
    Args:
        name: Optional name for the logger (defaults to 'llmXive')
        
    Returns:
        Logger instance
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logging()
    
    if name:
        return _default_logger.getChild(name)
    return _default_logger

# Custom exception hierarchy for the project
class LlmXiveError(Exception):
    """Base exception for llmXive project errors."""
    pass

class DataLoadError(LlmXiveError):
    """Raised when data loading fails."""
    pass

class ConfigurationError(LlmXiveError):
    """Raised when configuration validation fails."""
    pass

class SurrogateModelError(LlmXiveError):
    """Raised when surrogate model computation fails."""
    pass

class ValidationError(LlmXiveError):
    """Raised when validation checks fail."""
    pass

__all__ = [
    "setup_logging",
    "get_logger",
    "LlmXiveError",
    "DataLoadError",
    "ConfigurationError",
    "SurrogateModelError",
    "ValidationError"
]
