import logging
import sys
from datetime import datetime
import os

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Configure logging for the project.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs to console only.
    
    Returns:
        A configured logger instance.
    """
    # Create a custom formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    handlers = [console_handler]
    
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        handlers.append(file_handler)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates on re-calls
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    for handler in handlers:
        root_logger.addHandler(handler)
    
    return root_logger
