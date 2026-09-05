import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure the log directory exists
LOG_DIR = Path("data")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "run_logs.txt"

# Configure the root logger
logger_instance: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Configure the root logger to output to both console and a file.
    
    Args:
        log_file: Path to the log file. Defaults to data/run_logs.txt.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    global logger_instance
    
    if log_file is None:
        log_file = LOG_FILE
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    logger_instance = root_logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Name of the logger. If None, returns the root logger.
    
    Returns:
        A configured logger instance.
    """
    if logger_instance is None:
        setup_logging()
    
    if name is None:
        return logging.getLogger()
    
    return logging.getLogger(name)

# Initialize logging on module import if needed
# This ensures logging is available immediately
if logger_instance is None:
    setup_logging()