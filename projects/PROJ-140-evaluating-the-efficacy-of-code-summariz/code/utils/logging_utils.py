import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

# Ensure the logger is configured exactly once globally to prevent handler duplication
_logger_initialized = False

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_dir: Optional[str] = None,
    project_name: str = "llmXive"
) -> logging.Logger:
    """
    Configures and returns a project logger with file and console handlers.
    
    This function sets up the logging infrastructure for the project, creating
    a directory for logs if necessary, configuring a console handler, and
    optionally a file handler. It ensures handlers are not added multiple times
    if called repeatedly.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional specific filename for the log. If None, a timestamped file is created.
        log_dir: Optional directory for log files. Defaults to 'logs' in project root.
        project_name: Name to include in log prefixes.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    global _logger_initialized
    
    logger = logging.getLogger(project_name)
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
    else:
        # Default to a 'logs' directory relative to the script location (utils) -> project root
        # Assuming structure: code/utils/logging_utils.py -> project root is 2 levels up
        script_path = Path(__file__).resolve()
        log_path = script_path.parent.parent / "logs"
        log_path.mkdir(parents=True, exist_ok=True)
    
    if log_file:
        file_name = log_file
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{project_name}_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_path / file_name)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    _logger_initialized = True
    logger.info(f"Logging infrastructure initialized. Logs written to: {log_path / file_name}")
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves a logger instance. If a name is provided, it returns a child logger.
    If no logger has been set up yet, it initializes a default one.
    
    Args:
        name: Optional name for a child logger.
        
    Returns:
        logging.Logger: The logger instance.
    """
    logger_name = "llmXive"
    if name:
        logger_name = f"llmXive.{name}"
        
    logger = logging.getLogger(logger_name)
    
    # If no handlers exist, set up default logging
    if not logger.handlers:
        setup_logging()
        
    return logger

class ErrorHandler:
    """
    Utility class for handling and logging errors consistently.
    Provides structured error capture including stack traces and context.
    """
    
    @staticmethod
    def handle_error(e: Exception, context: str = "", level: int = logging.ERROR) -> None:
        """
        Logs an error with context and full stack trace.
        
        Args:
            e: The exception to log.
            context: Additional context string to prepend to the log message.
            level: The logging level to use.
        """
        logger = get_logger()
        msg = f"Error in {context}" if context else "An error occurred"
        logger.log(level, f"{msg}: {str(e)}", exc_info=True)

    @staticmethod
    def handle_critical_error(e: Exception, context: str = "") -> None:
        """
        Logs a critical error and optionally performs cleanup or exit.
        
        Args:
            e: The exception to log.
            context: Additional context string.
        """
        logger = get_logger()
        msg = f"CRITICAL ERROR in {context}" if context else "CRITICAL ERROR occurred"
        logger.critical(f"{msg}: {str(e)}", exc_info=True)
        # In a script context, we might want to re-raise or exit, 
        # but for a library utility, logging is the primary action.
        # Re-raising ensures the caller knows execution is compromised.
        raise e

    @staticmethod
    def log_warning(message: str, context: str = "") -> None:
        """
        Logs a warning message with optional context.
        
        Args:
            message: The warning message.
            context: Additional context string.
        """
        logger = get_logger()
        msg = f"{context}: {message}" if context else message
        logger.warning(msg)

    @staticmethod
    def log_info(message: str, context: str = "") -> None:
        """
        Logs an info message with optional context.
        
        Args:
            message: The info message.
            context: Additional context string.
        """
        logger = get_logger()
        msg = f"{context}: {message}" if context else message
        logger.info(msg)

# Initialize default logger on import if needed, or wait for explicit setup
# We avoid auto-setup on import to prevent file creation before config is loaded,
# but we ensure the root logger exists.
if not logging.getLogger("llmXive").handlers:
    # We don't auto-create files here to respect config loading order,
    # but we ensure the logger object is valid.
    pass
    
# Export public API
__all__ = ['setup_logging', 'get_logger', 'ErrorHandler']
