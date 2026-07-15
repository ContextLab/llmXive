"""
Base logging configuration for the llmXive project.
Provides a centralized logger that writes to a timestamped log file.
"""
import logging
import os
from pathlib import Path

# Define the log directory and file path relative to the project root
# Assuming this script is run from the project root or code/ directory
# The task specifies writing to code/logs/app.log
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"

# Ensure the log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Cache to store configured loggers
_loggers = {}

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    If the logger does not exist, it is created with a file handler 
    writing to code/logs/app.log and a specific format.
    
    Args:
        name (str): The name of the logger (usually __name__ of the module).
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding handlers multiple times if this function is called repeatedly
    if not logger.handlers:
        # Create file handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.DEBUG)

        # Create formatter with timestamp
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(file_handler)

        # Prevent propagation to root logger to avoid double logging if root is configured
        logger.propagate = False

    _loggers[name] = logger
    return logger
