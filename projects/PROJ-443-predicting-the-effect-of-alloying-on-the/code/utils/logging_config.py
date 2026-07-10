"""
Logging infrastructure configuration for the HEA Elastic Modulus project.

This module sets up a centralized logging system that:
1. Configures a root logger with appropriate handlers and formatters
2. Ensures consistent log formatting across all modules
3. Supports both console and file output
4. Adheres to the project's reproducibility and audit requirements
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict

# Project-specific constants
LOG_LEVELS = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_DIR = Path('logs')
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

_initialized = False
_config: Optional[Dict] = None


def get_log_level(level_str: str) -> int:
    """
    Convert a string log level to the corresponding logging constant.
    
    Args:
        level_str: Log level as a string (e.g., 'INFO', 'DEBUG')
        
    Returns:
        The corresponding logging constant integer
        
    Raises:
        ValueError: If the level string is not recognized
    """
    level_upper = level_str.upper()
    if level_upper not in LOG_LEVELS:
        valid_levels = ', '.join(LOG_LEVELS.keys())
        raise ValueError(f"Invalid log level '{level_str}'. Valid levels: {valid_levels}")
    return LOG_LEVELS[level_upper]


def setup_logging(
    log_level: str = DEFAULT_LOG_LEVEL,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True,
    format_string: Optional[str] = None
) -> None:
    """
    Configure the root logger for the entire application.
    
    This function should be called once at the start of the application
    before any other logging occurs.
    
    Args:
        log_level: Minimum log level (e.g., 'INFO', 'DEBUG')
        log_dir: Directory for log files. Defaults to 'logs/' relative to project root.
        log_file: Specific log filename. Defaults to 'pipeline.log' if not provided.
        console_output: Whether to log to console (stderr). Defaults to True.
        file_output: Whether to log to file. Defaults to True.
        format_string: Custom log format string. Uses default if None.
        
    Raises:
        ValueError: If log_level is invalid
        RuntimeError: If called more than once (logging already initialized)
    """
    global _initialized, _config
    
    if _initialized:
        logging.warning("Logging already initialized. Ignoring subsequent setup_logging calls.")
        return
    
    # Validate log level
    level = get_log_level(log_level)
    
    # Determine log directory and file
    if log_dir is None:
        log_dir = Path.cwd() / DEFAULT_LOG_DIR
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if log_file is None:
        log_file = 'pipeline.log'
    
    log_path = log_dir / log_file
    
    # Create formatter
    fmt = format_string if format_string else DEFAULT_LOG_FORMAT
    formatter = logging.Formatter(fmt, datefmt=DATE_FORMAT)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Add console handler if requested
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Add file handler if requested
    if file_output:
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Store config for reference
    _config = {
        'level': log_level,
        'log_dir': str(log_dir),
        'log_file': log_file,
        'console_output': console_output,
        'file_output': file_output
    }
    
    _initialized = True
    
    logging.info(f"Logging initialized at level {log_level}")
    logging.info(f"Log file: {log_path}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a specific name.
    
    Args:
        name: Logger name (module name is typical). If None, returns root logger.
        
    Returns:
        A configured Logger instance
        
    Raises:
        RuntimeError: If logging has not been initialized yet
    """
    if not _initialized:
        # Auto-initialize with defaults if not explicitly set up
        setup_logging()
    
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)


def configure_module_logging(module_name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for a specific module.
    
    Args:
        module_name: The module name (e.g., 'utils.data_fetch')
        log_level: Optional override log level for this module
        
    Returns:
        Configured logger for the module
    """
    logger = get_logger(module_name)
    if log_level:
        logger.setLevel(get_log_level(log_level))
    return logger


def is_logging_initialized() -> bool:
    """Check if logging has been initialized."""
    return _initialized


def get_current_config() -> Optional[Dict]:
    """Return the current logging configuration if initialized."""
    return _config.copy() if _config else None