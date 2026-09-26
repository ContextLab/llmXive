"""
Logging utilities.
"""
import logging
import os
from pathlib import Path
from typing import Optional

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with a specific name.
    
    Args:
        name: Logger name.
        log_file: Optional path to log file.
        
    Returns:
        Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler if specified
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
            
    return logger

def test_logging():
    """Test the logging setup."""
    logger = get_logger("test", "logs/test.log")
    logger.info("Test log message")
    print("Logging test completed. Check logs/test.log")

if __name__ == '__main__':
    test_logging()