"""
Logging Infrastructure for llmXive.

Provides centralized logging configuration and helper functions.
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any

# Default log directory
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Global configuration for logging
_log_config: Dict[str, Any] = {
    "initialized": False,
    "level": logging.INFO,
    "project_id": "llmxive"
}

def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    project_id: str = "llmxive",
    console_level: Optional[int] = None,
    file_level: Optional[int] = None
) -> logging.Logger:
    """
    Configure the root logger for the project.
    
    This function sets up a root logger with both console and file handlers.
    It ensures that log messages are formatted consistently and that log files
    are rotated to prevent disk space issues.
    
    Args:
        log_file: Optional filename for file logging. Defaults to {project_id}.log.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        project_id: Identifier for the log file and default logger name.
        console_level: Optional override for console handler level. Defaults to `level`.
        file_level: Optional override for file handler level. Defaults to `level`.
        
    Returns:
        Configured root logger instance.
    """
    global _log_config
    
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler_level = console_level if console_level is not None else level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_handler_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    if log_file:
        log_path = LOG_DIR / log_file
    else:
        log_path = LOG_DIR / f"{project_id}.log"
        
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler_level = file_level if file_level is not None else level
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10*1024*1024, # 10 MB
        backupCount=5
    )
    file_handler.setLevel(file_handler_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Update config state
    _log_config["initialized"] = True
    _log_config["level"] = level
    _log_config["project_id"] = project_id
    
    return logger

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    This is the primary entry point for obtaining a logger in any module.
    If the root logger hasn't been configured yet via `setup_logging`, 
    this will return a logger with default settings (INFO level, console only).
    
    Args:
        name: Logger name, typically the module name (__name__) or a custom identifier.
        
    Returns:
        Logger instance.
    """
    if not _log_config["initialized"]:
        # Auto-configure if not done yet to ensure logging works immediately
        setup_logging(project_id="llmxive")
    
    return logging.getLogger(name)

def log_exception(logger: logging.Logger, exc: Exception, msg: str = "An exception occurred"):
    """
    Log an exception with full traceback information.
    
    Args:
        logger: Logger instance to use.
        exc: Exception instance to log.
        msg: Optional message prefix to include before the exception details.
    """
    logger.exception(f"{msg}: {exc}")

def log_critical(logger: logging.Logger, msg: str):
    """
    Log a critical message indicating a severe error condition.
    
    Args:
        logger: Logger instance to use.
        msg: Message to log.
    """
    logger.critical(msg)

def log_warning(logger: logging.Logger, msg: str):
    """
    Log a warning message indicating a potential issue.
    
    Args:
        logger: Logger instance to use.
        msg: Message to log.
    """
    logger.warning(msg)

def log_info(logger: logging.Logger, msg: str):
    """
    Log an informational message.
    
    Args:
        logger: Logger instance to use.
        msg: Message to log.
    """
    logger.info(msg)

def log_debug(logger: logging.Logger, msg: str):
    """
    Log a debug message for detailed troubleshooting.
    
    Args:
        logger: Logger instance to use.
        msg: Message to log.
    """
    logger.debug(msg)

def set_log_level(level: int) -> None:
    """
    Dynamically update the logging level for all handlers.
    
    Args:
        level: The new logging level (e.g., logging.DEBUG).
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

def get_log_directory() -> Path:
    """
    Get the path to the log directory.
    
    Returns:
        Path object pointing to the log directory.
    """
    return LOG_DIR