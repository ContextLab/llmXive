import logging
import os
import sys
from pathlib import Path
from config import LOGS_DIR

def setup_logger(
    name: str = "llmXive",
    level: int = logging.INFO,
    log_file: str = "pipeline.log",
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
) -> logging.Logger:
    """
    Configure and return a logger instance that writes to both stdout and a file.
    
    Args:
        name: Logger name (default: "llmXive")
        level: Logging level (default: logging.INFO)
        log_file: Filename relative to LOGS_DIR (default: "pipeline.log")
        format_str: Log format string
    
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger
    
    # Ensure logs directory exists
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # File handler
    file_path = Path(LOGS_DIR) / log_file
    fh = logging.FileHandler(file_path)
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(format_str))
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(format_str))
    
    # Add handlers
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve an existing logger or create a default one if it doesn't exist.
    
    Args:
        name: Logger name
    
    Returns:
        logging.Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # If no handlers exist, set up default configuration
        return setup_logger(name=name)
    return logger