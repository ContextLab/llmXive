import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

class LoggerError(Exception):
    """Custom exception for logger configuration failures."""
    pass

class LogConfigurationError(Exception):
    """Custom exception for log configuration errors."""
    pass

_logger_instance: Optional[logging.Logger] = None

def configure_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Configure the root logger for the project.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Optional path to log file
    """
    global _logger_instance
    
    if _logger_instance is not None:
        return
    
    try:
        logger = logging.getLogger('llmXive')
        logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        _logger_instance = logger
    except Exception as e:
        raise LogConfigurationError(f"Failed to configure logging: {str(e)}")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance.
    """
    global _logger_instance
    
    if _logger_instance is None:
        configure_logging()
    
    return logging.getLogger(f'llmXive.{name}')
