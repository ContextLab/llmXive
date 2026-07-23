"""
Logging configuration module.

Sets up logging to both file and stdout with appropriate formatting.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional
from config.env_config import get_config, get_log_file_path, get_log_level

def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Configure logging to output to both file and stdout.
    
    Args:
        log_level: Optional log level override (e.g., 'DEBUG', 'INFO')
        
    Returns:
        Root logger instance
    """
    if log_level is None:
        log_level = get_log_level()
    
    # Ensure log directory exists
    log_file_path = get_log_file_path()
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def main():
    """
    Main entry point for logging configuration demonstration.
    """
    setup_logging()
    logger = get_logger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

if __name__ == "__main__":
    main()
