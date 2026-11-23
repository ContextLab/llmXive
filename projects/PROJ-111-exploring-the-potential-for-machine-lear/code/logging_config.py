import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from config import get_config

def setup_logging():
    """
    Configure the logging system.
    Creates a logger with a file handler and a console handler.
    Logs are saved to a timestamped file in the logs directory.
    """
    config = get_config()
    log_dir = Path(config.log_dir) if hasattr(config, 'log_dir') else Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"data_generation_{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    logger.info(f"Logging initialized. Log file: {log_file}")
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    Ensures the logger is configured if setup_logging hasn't been called yet.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # If no handlers, it means setup_logging might not have been called or this is a child logger
        # We rely on the root logger configuration if setup_logging was called first.
        # If not, we might need to call setup_logging here, but typically setup_logging is called in main.
        pass
    return logger
