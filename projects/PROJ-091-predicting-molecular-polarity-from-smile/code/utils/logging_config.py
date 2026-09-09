import logging
import json
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Standardized format string as per T039c requirement
STANDARD_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class JsonFormatter(logging.Formatter):
    """Custom formatter for JSON structured logging."""
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'name': record.name,
            'levelname': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def get_project_root() -> Path:
    """Returns the project root directory (parent of 'code')."""
    current_file = Path(__file__).resolve()
    # Assuming code/utils/logging_config.py -> root is 2 levels up
    return current_file.parent.parent

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configures the root logger with the standardized format.
    
    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional relative path to a log file (e.g., 'logs/app.log').
    """
    # Get the standardized format string
    fmt = STANDARD_LOG_FORMAT
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(fmt))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        project_root = get_project_root()
        log_path = project_root / log_file
        
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use RotatingFileHandler as per T008 requirement
        file_handler = RotatingFileHandler(
            log_path, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        # Apply standardized format to file handler too
        file_handler.setFormatter(logging.Formatter(fmt))
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieves a logger with the specified name.
    
    Args:
        name: The name of the logger (typically __name__).
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)

def set_log_level(level: int) -> None:
    """Sets the global log level for all handlers."""
    logger = logging.getLogger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)

def log_with_context(logger: logging.Logger, level: int, message: str, context: Optional[dict] = None) -> None:
    """
    Logs a message with optional context.
    
    Args:
        logger: The logger instance.
        level: The log level.
        message: The message to log.
        context: Optional dictionary of context to include.
    """
    if context:
        full_message = f"{message} | Context: {json.dumps(context)}"
        logger.log(level, full_message)
    else:
        logger.log(level, message)
