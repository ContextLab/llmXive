import logging
import os
from pathlib import Path
from config import OUTPUTS_LOGS_DIR, LOG_LEVEL, LOG_FILE

def setup_logger(name: str, level: int = LOG_LEVEL) -> logging.Logger:
    """
    Setup a logger with file and console handlers.
    
    Args:
        name: Name of the logger.
        level: Logging level.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # Create file handler
    log_file = LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
