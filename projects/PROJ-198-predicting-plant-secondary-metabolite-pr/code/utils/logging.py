"""
Logging infrastructure setup for llmXive pipeline.

Provides centralized logging configuration with support for:
- Console output (stdout)
- File output (rotating or single file)
- Custom log levels
- Module-specific loggers

Usage:
    from utils.logging import setup_logging, get_logger
    
    # Initialize logging at entry point
    setup_logging(log_level=logging.INFO, log_file=Path("data/logs/pipeline.log"))
    
    # Get logger in any module
    logger = get_logger("data.download")
    logger.info("Starting download...")
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

# Module-level singleton for the root logger
_logger: Optional[logging.Logger] = None
_setup_called: bool = False

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
MAX_LOG_BYTES = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[Path] = None,
    console: bool = True,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    max_bytes: int = MAX_LOG_BYTES,
    backup_count: int = BACKUP_COUNT
) -> logging.Logger:
    """
    Configure the root logger with file and console handlers.
    
    This function sets up the logging infrastructure for the entire pipeline.
    It should be called once at the entry point of the application.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to log file. If None, only console output is enabled.
                  If the parent directory doesn't exist, it will be created.
        console: Whether to log to console (stdout).
        log_format: Custom log format string. Uses default if None.
        date_format: Custom date format for timestamps. Uses default if None.
        max_bytes: Maximum size of log file before rotation (for file handler).
        backup_count: Number of backup files to keep (for rotating file handler).
                      
    Returns:
        Configured root logger instance.
        
    Raises:
        ValueError: If log_level is invalid.
        OSError: If log file cannot be created.
        
    Example:
        >>> from utils.logging import setup_logging
        >>> import logging
        >>> from pathlib import Path
        >>> logger = setup_logging(
        ...     log_level=logging.DEBUG,
        ...     log_file=Path("data/logs/pipeline.log"),
        ...     console=True
        ... )
    """
    global _logger, _setup_called
    
    # Prevent re-initialization
    if _setup_called and _logger is not None:
        _logger.debug("Logging already configured, returning existing logger")
        return _logger
    
    # Validate log level
    if not isinstance(log_level, int) or log_level not in [
        logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL
    ]:
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Create or get root logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates on re-call
    logger.handlers.clear()
    
    # Set up formatters
    fmt = log_format or DEFAULT_LOG_FORMAT
    date_fmt = date_format or DEFAULT_LOG_DATE_FORMAT
    formatter = logging.Formatter(fmt, datefmt=date_fmt)
    
    # Console Handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(log_level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        _logger.debug("Console handler added")
    
    # File Handler (with rotation)
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Use RotatingFileHandler for automatic log rotation
        try:
            fh = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            _logger.debug(f"File handler added: {log_file}")
        except OSError as e:
            # If file handler fails, log to console and warn
            console_fallback = logging.StreamHandler(sys.stdout)
            console_fallback.setLevel(logging.WARNING)
            console_fallback.setFormatter(formatter)
            logger.addHandler(console_fallback)
            logger.error(f"Failed to create file handler for {log_file}: {e}")
            logger.warning("Falling back to console-only logging")
    
    _logger = logger
    _setup_called = True
    
    logger.info("Logging infrastructure initialized")
    logger.debug(f"Log level: {logging.getLevelName(log_level)}")
    logger.debug(f"Console output: {console}")
    logger.debug(f"Log file: {log_file}")
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a sub-logger name.
    
    This function ensures logging is initialized before returning a logger.
    If logging hasn't been set up yet, it calls setup_logging() with defaults.
    
    Args:
        name: Sub-logger name (e.g., "llmXive.data", "llmXive.modeling").
              If None, returns the root logger.
              
    Returns:
        Logger instance.
        
    Example:
        >>> from utils.logging import get_logger
        >>> logger = get_logger("data.download")
        >>> logger.info("Downloading genomes...")
    """
    global _logger
    
    # Auto-initialize if not already done
    if _logger is None:
        setup_logging()
    
    if name:
        return logging.getLogger(f"llmXive.{name}")
    return _logger

def reset_logging() -> None:
    """
    Reset logging configuration to initial state.
    
    This clears all handlers and resets the singleton logger.
    Useful for testing or re-configuring logging.
    
    Note: This should be used with caution in production code.
    """
    global _logger, _setup_called
    
    # Clear handlers on root logger
    root_logger = logging.getLogger("llmXive")
    root_logger.handlers.clear()
    root_logger.setLevel(logging.NOTSET)
    
    # Reset module state
    _logger = None
    _setup_called = False

def get_log_file_path(log_file: Optional[Path] = None) -> Optional[Path]:
    """
    Get the current log file path if file logging is enabled.
    
    Args:
        log_file: Optional path to check. If None, returns the currently
                  configured log file path.
                  
    Returns:
        Path to log file if configured, None otherwise.
    """
    if log_file:
        return log_file
    
    # Check if file handler exists
    logger = logging.getLogger("llmXive")
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler):
            return Path(handler.baseFilename)
    
    return None