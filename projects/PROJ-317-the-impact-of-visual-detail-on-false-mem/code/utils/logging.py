"""
Logging utilities with automatic PII sanitization.

This module provides logging configuration and utilities that automatically
sanitize log messages to prevent PII leakage.
"""
import logging
import os
from pathlib import Path
from typing import Optional
from config import get_logs_dir, get_log_file_path as config_get_log_file_path, \
    get_error_log_file_path as config_get_error_log_file_path, \
    get_manipulation_error_log_path as config_get_manipulation_error_log_path
from utils.security import SanitizedLogger, sanitize_log_message

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> SanitizedLogger:
    """
    Get a sanitized logger instance.
    
    Args:
        name: Name for the logger.
        
    Returns:
        A SanitizedLogger instance that automatically masks PII.
    """
    return SanitizedLogger(name)

def get_log_file_path() -> Path:
    """
    Get the path to the main log file.
    
    Returns:
        Path to the log file.
    """
    return config_get_log_file_path()

def get_error_log_file_path() -> Path:
    """
    Get the path to the error log file.
    
    Returns:
        Path to the error log file.
    """
    return config_get_error_log_file_path()

def get_manipulation_error_log_path() -> Path:
    """
    Get the path to the manipulation error log file.
    
    Returns:
        Path to the manipulation error log file.
    """
    return config_get_manipulation_error_log_path()

def sanitize_message(message: str) -> str:
    """
    Sanitize a message to remove PII.
    
    This is a convenience function that wraps the security module's
    sanitization functionality.
    
    Args:
        message: The message to sanitize.
        
    Returns:
        Sanitized message with PII masked.
    """
    return sanitize_log_message(message)

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    console_output: bool = True
) -> None:
    """
    Configure the logging system with PII sanitization.
    
    This function sets up logging to both console and file, ensuring that
    all log messages are automatically sanitized to prevent PII leakage.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to log file. If None, uses default path.
        console_output: If True, log to console as well as file.
    """
    # Ensure logs directory exists
    logs_dir = get_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Use default log file if none provided
    if log_file is None:
        log_file = get_log_file_path()
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Create console handler if requested
    handlers = [file_handler]
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        handlers.append(console_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Add custom formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    for handler in handlers:
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    
    # Log startup message (will be sanitized)
    logger = get_logger()
    logger.info("Logging system initialized with PII sanitization enabled")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {log_level}")

def ensure_error_log_directory() -> Path:
    """
    Ensure the error log directory exists.
    
    Returns:
        Path to the error log directory.
    """
    error_log_dir = get_error_log_file_path().parent
    error_log_dir.mkdir(parents=True, exist_ok=True)
    return error_log_dir

def log_error(message: str, error_log_path: Optional[Path] = None) -> None:
    """
    Log an error message to the error log file with PII sanitization.
    
    This function is specifically designed to log errors to the error log
    file while ensuring no PII is leaked.
    
    Args:
        message: The error message to log.
        error_log_path: Optional path to error log file. If None, uses default.
    """
    if error_log_path is None:
        error_log_path = get_error_log_file_path()
    
    # Ensure directory exists
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sanitize the message
    sanitized_message = sanitize_log_message(message)
    
    # Get or create error logger
    error_logger = logging.getLogger("error_logger")
    error_logger.setLevel(logging.ERROR)
    
    # Remove existing handlers
    error_logger.handlers.clear()
    
    # Add file handler
    file_handler = logging.FileHandler(error_log_path, encoding='utf-8')
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    error_logger.addHandler(file_handler)
    
    # Log the error
    error_logger.error(sanitized_message)

def log_manipulation_error(image_id: str, error_message: str) -> None:
    """
    Log a manipulation error to the specific manipulation error log.
    
    This function logs errors that occur during image manipulation to a
    dedicated log file, with PII sanitization applied.
    
    Args:
        image_id: The ID of the image that failed manipulation.
        error_message: The error message describing the failure.
    """
    error_path = get_manipulation_error_log_path()
    
    # Ensure directory exists
    error_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sanitize the message
    sanitized_message = sanitize_log_message(
        f"Image {image_id} failed manipulation: {error_message}"
    )
    
    # Log to file
    with open(error_path, 'a', encoding='utf-8') as f:
        f.write(f"{sanitized_message}\n")

# Initialize default logging configuration when module is imported
# This can be overridden by calling setup_logging() with custom parameters
try:
    setup_logging()
except Exception:
    # If setup fails (e.g., config not loaded), use basic configuration
    logging.basicConfig(level=logging.INFO)
    logging.getLogger().warning("Using basic logging configuration")