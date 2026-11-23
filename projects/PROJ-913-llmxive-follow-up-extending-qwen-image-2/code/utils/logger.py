import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from config import PROJECT_ROOT

_logger_instance: Optional[logging.Logger] = None

def setup_global_logger(name: str = "llmXive", level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a global logger with file rotation.
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance

    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{name}.log"

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _logger_instance = logger
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves the logger, creating it if necessary.
    """
    return setup_global_logger(name)
