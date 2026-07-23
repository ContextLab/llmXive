"""
Logging configuration for the research pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a logger instance with the specified name and level.
    
    Args:
        name: Logger name (usually __name__).
        level: Logging level.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # Create console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        ch.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(ch)
        
    return logger

def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger for the entire application.
    
    Args:
        level: Logging level for the root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    if not root_logger.handlers:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        ch.setFormatter(formatter)
        root_logger.addHandler(ch)

def main():
    """Test logging configuration."""
    configure_root_logger()
    logger = get_logger(__name__)
    logger.info("Logging configuration test successful")

if __name__ == "__main__":
    main()
