import logging
import sys
import os
from pathlib import Path
from typing import Optional

from config import get_config

_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None

def setup_logger(
    name: str = "llmXive",
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    use_color: bool = True
) -> logging.Logger:
    """
    Configure the global logger instance for the pipeline.
    
    Args:
        name: Logger name.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If provided, logs are written there.
        use_color: Whether to use ANSI color codes in console output.
    
    Returns:
        The configured logger instance.
    """
    global _logger, _handler
    
    if _logger is not None:
        return _logger

    config = get_config()
    if level is None:
        # Default to INFO unless DEBUG is explicitly set in config
        level_str = config.get("logging", {}).get("level", "INFO")
        level = getattr(logging, level_str.upper(), logging.INFO)

    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    
    # Prevent adding multiple handlers if called multiple times
    if _logger.handlers:
        return _logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Simple formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    return _logger

def get_pipeline_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve the initialized pipeline logger.
    If not initialized, initializes it with default settings from config.
    
    Args:
        name: Logger name (default 'llmXive').
    
    Returns:
        The logger instance.
    """
    global _logger
    if _logger is None:
        # Initialize with defaults if not explicitly set up yet
        _logger = setup_logger(name)
    return _logger

def log_error(error: Exception, context: str = "Pipeline Error") -> None:
    """
    Log an exception with context using the pipeline logger.
    
    Args:
        error: The exception to log.
        context: A string describing the context where the error occurred.
    """
    logger = get_pipeline_logger()
    logger.error(f"{context}: {error.__class__.__name__} - {str(error)}")
    logger.debug(f"Traceback: {''.join(__import__('traceback').format_exception(type(error), error, error.__traceback__))}")

def log_warning(message: str) -> None:
    """
    Log a warning message.
    
    Args:
        message: The warning message.
    """
    logger = get_pipeline_logger()
    logger.warning(message)

def log_info(message: str) -> None:
    """
    Log an info message.
    
    Args:
        message: The info message.
    """
    logger = get_pipeline_logger()
    logger.info(message)

def log_debug(message: str) -> None:
    """
    Log a debug message.
    
    Args:
        message: The debug message.
    """
    logger = get_pipeline_logger()
    logger.debug(message)
