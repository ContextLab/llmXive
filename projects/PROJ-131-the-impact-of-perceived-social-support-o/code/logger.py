import logging
from pathlib import Path
import sys

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance with consistent formatting.
    
    Args:
        name: The name of the logger (typically __name__)
    
    Returns:
        A configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if not already present to avoid duplicates
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger
