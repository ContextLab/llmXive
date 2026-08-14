import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_logger_instance = None
_log_setup = False

def setup_logging(level: str = "INFO", log_dir: Optional[str] = None) -> logging.Logger:
    """
    Initialize the logging system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Optional directory to write log files. If None, logs to console only.
    
    Returns:
        The root logger instance.
    """
    global _logger_instance, _log_setup
    
    if _log_setup:
        return _logger_instance
    
    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"llmxive_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)
    
    _logger_instance = logger
    _log_setup = True
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (module name). If None, returns root logger.
    
    Returns:
        Logger instance.
    """
    if not _log_setup:
        setup_logging()
    
    return logging.getLogger(name) if name else _logger_instance

def reset_logging():
    """Reset the logging configuration."""
    global _logger_instance, _log_setup
    logging.getLogger().handlers.clear()
    _logger_instance = None
    _log_setup = False

# Convenience functions
def debug(msg: str):
    get_logger().debug(msg)

def info(msg: str):
    get_logger().info(msg)

def warning(msg: str):
    get_logger().warning(msg)

def error(msg: str):
    get_logger().error(msg)

def critical(msg: str):
    get_logger().critical(msg)

def exception(msg: str):
    get_logger().exception(msg)
