"""
Logging configuration utility for the llmXive pipeline.

This module sets up a centralized logging infrastructure that writes to
data/logs/pipeline.log while also providing console output for interactive use.
"""
import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Default log file path relative to project root
DEFAULT_LOG_PATH = "data/logs/pipeline.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5

# Global logger instance reference
_logger = None


def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Get or create a logger instance with the specified name.
    
    Args:
        name: Logger name, defaults to "pipeline"
        
    Returns:
        Configured logging.Logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return logging.getLogger(name)


def setup_logging(
    log_path: str = DEFAULT_LOG_PATH,
    log_level: int = DEFAULT_LOG_LEVEL,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT
) -> logging.Logger:
    """
    Configure the logging infrastructure.
    
    Creates the log directory if it doesn't exist, sets up a rotating file
    handler for persistent logging, and a console handler for real-time output.
    
    Args:
        log_path: Relative path to the log file (default: data/logs/pipeline.log)
        log_level: Logging level (default: INFO)
        max_bytes: Maximum size of log file before rotation (default: 10MB)
        backup_count: Number of backup log files to keep (default: 5)
        
    Returns:
        The root logger with configured handlers
    """
    # Ensure the log directory exists
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatter with detailed output
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except (OSError, IOError) as e:
        # Fallback to basic file handler if RotatingFileHandler fails
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Console handler for real-time visibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    return root_logger


def log_pipeline_start(script_name: str) -> None:
    """
    Log the start of a pipeline script.
    
    Args:
        script_name: Name of the script starting
    """
    logger = get_logger()
    logger.info(f"Pipeline script '{script_name}' starting...")


def log_pipeline_end(script_name: str, success: bool = True) -> None:
    """
    Log the end of a pipeline script.
    
    Args:
        script_name: Name of the script ending
        success: Whether the script completed successfully
    """
    logger = get_logger()
    status = "successfully" if success else "with errors"
    logger.info(f"Pipeline script '{script_name}' completed {status}.")


def log_error_occurrence(script_name: str, error: Exception) -> None:
    """
    Log an error occurrence during pipeline execution.
    
    Args:
        script_name: Name of the script where error occurred
        error: The exception that was raised
    """
    logger = get_logger()
    logger.error(f"Error in '{script_name}': {str(error)}", exc_info=True)
