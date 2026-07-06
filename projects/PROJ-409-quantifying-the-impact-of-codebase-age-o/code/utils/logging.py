"""
Unified logging configuration for the llmXive pipeline.

Provides a consistent logging interface across all modules with:
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Timestamped output
- Separate handlers for console and file output
- Support for colored console output (optional)
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Literal

# Default log level
DEFAULT_LEVEL = logging.INFO

# Log format string
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Cache for configured loggers to avoid re-configuration
_configured = False

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the unified configuration.
    
    Args:
        name: Optional logger name. If None, returns the root logger.
    
    Returns:
        A configured logging.Logger instance.
    """
    if not _configured:
        setup_logging()
    
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)

def setup_logging(
    level: int = DEFAULT_LEVEL,
    log_file: Optional[str] = None,
    console: bool = True,
    file: bool = True,
    log_dir: Optional[str] = None
) -> None:
    """
    Configure the root logger with unified settings.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional filename for log output. If None, uses default naming.
        console: Whether to log to console.
        file: Whether to log to file.
        log_dir: Directory for log files. Defaults to 'data/logs/'.
    """
    global _configured
    
    # Prevent re-configuration if already done
    if _configured:
        return
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if file:
        if log_dir is None:
            log_dir = "data/logs"
        
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        if log_file is None:
            import time
            log_file = f"pipeline_{time.strftime('%Y%m%d_%H%M%S')}.log"
        
        file_path = log_path / log_file
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    _configured = True

def set_log_level(level: int) -> None:
    """
    Update the logging level for the root logger and all handlers.
    
    Args:
        level: New logging level (e.g., logging.DEBUG).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in root_logger.handlers:
        handler.setLevel(level)

def get_level_name(level: int) -> str:
    """
    Get the string name of a logging level.
    
    Args:
        level: Logging level integer.
    
    Returns:
        String name (e.g., 'INFO', 'DEBUG').
    """
    return logging.getLevelName(level)

# Convenience functions for common log levels
def debug(msg: str, *args, **kwargs) -> None:
    """Log a debug message."""
    get_logger().debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs) -> None:
    """Log an info message."""
    get_logger().info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs) -> None:
    """Log a warning message."""
    get_logger().warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs) -> None:
    """Log an error message."""
    get_logger().error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs) -> None:
    """Log a critical message."""
    get_logger().critical(msg, *args, **kwargs)

def exception(msg: str, *args, **kwargs) -> None:
    """Log an error message with exception traceback."""
    get_logger().exception(msg, *args, **kwargs)

# Initialize logging on import with default settings
# This ensures logging is ready for immediate use
setup_logging(level=DEFAULT_LEVEL)

__all__ = [
    'get_logger',
    'setup_logging',
    'set_log_level',
    'get_level_name',
    'debug',
    'info',
    'warning',
    'error',
    'critical',
    'exception',
    'DEFAULT_LEVEL',
    'LOG_FORMAT',
    'DATE_FORMAT'
]
