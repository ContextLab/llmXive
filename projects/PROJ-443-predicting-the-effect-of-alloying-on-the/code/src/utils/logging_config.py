"""
Logging configuration and utility functions for the HEA Elastic Modulus project.

Provides a centralized logging setup that ensures consistent formatting,
log levels, and output destinations across all modules.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import os

# Global state to track initialization
_logging_initialized: bool = False
_current_config: Optional[Dict[str, str]] = None
_logger_instance: Optional[logging.Logger] = None

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def get_log_level(level_str: str) -> int:
    """
    Convert a string log level to the corresponding logging constant.
    
    Args:
        level_str: String representation of log level (e.g., 'INFO', 'DEBUG')
        
    Returns:
        The corresponding logging constant (e.g., logging.INFO)
        
    Raises:
        ValueError: If the level string is not recognized
    """
    level_str = level_str.upper()
    if level_str in LOG_LEVELS:
        return LOG_LEVELS[level_str]
    raise ValueError(f"Invalid log level: {level_str}. Valid levels: {list(LOG_LEVELS.keys())}")

def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    format_str: Optional[str] = None,
    date_format: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = False,
) -> None:
    """
    Configure the root logger with specified settings.
    
    This function sets up logging handlers for console and/or file output,
    configures the log format, and sets the global initialization state.
    
    Args:
        level: Log level as a string (e.g., 'INFO', 'DEBUG'). Defaults to 'INFO'.
        log_file: Path to log file. If provided and file_output is True, logs are written here.
        format_str: Custom log format string. Defaults to DEFAULT_FORMAT.
        date_format: Custom date format string. Defaults to DEFAULT_DATE_FORMAT.
        console_output: If True, add a console handler. Defaults to True.
        file_output: If True and log_file is provided, add a file handler. Defaults to False.
        
    Raises:
        ValueError: If log_file is provided but file_output is True and path is invalid
    """
    global _logging_initialized, _current_config

    # Set default values
    level = level or "INFO"
    format_str = format_str or DEFAULT_FORMAT
    date_format = date_format or DEFAULT_DATE_FORMAT

    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(get_log_level(level))

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(fmt=format_str, datefmt=date_format)

    # Add console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(get_log_level(level))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Add file handler if requested
    if file_output and log_file:
        if not isinstance(log_file, Path):
            log_file = Path(log_file)
        
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setLevel(get_log_level(level))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Update global state
    _logging_initialized = True
    _current_config = {
        "level": level,
        "log_file": str(log_file) if log_file else None,
        "format": format_str,
        "date_format": date_format,
        "console_output": console_output,
        "file_output": file_output,
        "timestamp": datetime.now().isoformat(),
    }

    # Log initialization
    root_logger.info(f"Logging initialized with level: {level}")
    if log_file and file_output:
        root_logger.info(f"Log file: {log_file}")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    If logging is not yet initialized, this function will call init_default_logging()
    to set up a basic configuration.
    
    Args:
        name: Name for the logger. If None, the root logger is returned.
            
    Returns:
        A logging.Logger instance
    """
    if not _logging_initialized:
        init_default_logging()
    
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)

def configure_module_logging(
    module_name: str,
    level: Optional[str] = None,
    propagate: bool = False,
) -> logging.Logger:
    """
    Configure logging for a specific module.
    
    This is useful for setting different log levels for specific modules
    while maintaining a consistent global configuration.
    
    Args:
        module_name: The name of the module (e.g., 'src.data.fetch_oqmd')
        level: Optional log level override for this module
        propagate: If False, prevent log messages from being passed to parent handlers
            
    Returns:
        A configured logger instance for the module
    """
    logger = logging.getLogger(module_name)
    
    if level:
        logger.setLevel(get_log_level(level))
    
    logger.propagate = propagate
    
    if not _logging_initialized:
        init_default_logging()
    
    return logger

def is_logging_initialized() -> bool:
    """
    Check if logging has been initialized.
    
    Returns:
        True if logging is initialized, False otherwise
    """
    return _logging_initialized

def get_current_config() -> Optional[Dict[str, str]]:
    """
    Get the current logging configuration.
    
    Returns:
        A dictionary containing the current configuration, or None if not initialized
    """
    return _current_config.copy() if _current_config else None

def init_default_logging() -> None:
    """
    Initialize logging with default settings.
    
    This is called automatically by get_logger() if logging hasn't been
    explicitly configured yet. It sets up console output with INFO level.
    """
    global _logging_initialized
    
    if _logging_initialized:
        return
    
    setup_logging(
        level="INFO",
        console_output=True,
        file_output=False,
    )
    
    _logging_initialized = True

# Convenience function for quick logging setup in scripts
def init_script_logging(script_name: str, log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Initialize logging for a script with file output.
    
    This creates a log file named after the script in the specified directory
    (or a default 'logs' directory if none is provided).
    
    Args:
        script_name: Name of the script (used for log file naming)
        log_dir: Directory for log files. Defaults to 'logs' in the current working directory.
            
    Returns:
        A configured logger instance
    """
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    
    log_file = log_dir / f"{script_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    setup_logging(
        level="DEBUG",
        log_file=log_file,
        console_output=True,
        file_output=True,
        format_str=f"%(asctime)s - {script_name} - %(name)s - %(levelname)s - %(message)s"
    )
    
    return get_logger(script_name)

# Initialize default logging immediately for immediate use
# This ensures that any module importing this file gets a working logger
init_default_logging()
