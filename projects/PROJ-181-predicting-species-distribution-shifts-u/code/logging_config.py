import logging
import os
import sys
from pathlib import Path
from config import LOGS_DIR

class DetailedFormatter(logging.Formatter):
    """Custom formatter that includes timestamp, level, and module name."""
    
    def format(self, record):
        log_fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        self._style._fmt = log_fmt
        return super().format(record)

def setup_logger(name: str = "llmXive", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger that writes to both console and log files.
    
    Args:
        name: Logger name (default: "llmXive")
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = DetailedFormatter()
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # File handler (detailed)
    log_file = LOGS_DIR / "pipeline.log"
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler (simple)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get an existing logger or create a new one if it doesn't exist.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name, logger.level)
    return logger
