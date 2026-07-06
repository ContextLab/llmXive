import logging
import os
import sys
from pathlib import Path
from typing import Optional

_logger_instance: Optional[logging.Logger] = None

def configure_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """Configure the root logger."""
    global _logger_instance
    
    if _logger_instance is not None:
        return # Already configured

    _logger_instance = logging.getLogger("llmXive")
    _logger_instance.setLevel(log_level)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    _logger_instance.addHandler(ch)
    
    # File handler if requested
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        _logger_instance.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name, ensuring global config is set."""
    if _logger_instance is None:
        configure_logging()
    return logging.getLogger(name)

def set_log_level(level: int) -> None:
    """Set the log level for the root logger."""
    if _logger_instance:
        _logger_instance.setLevel(level)
    else:
        configure_logging(log_level=level)

def debug(msg): get_logger(__name__).debug(msg)
def info(msg): get_logger(__name__).info(msg)
def warning(msg): get_logger(__name__).warning(msg)
def error(msg): get_logger(__name__).error(msg)
def critical(msg): get_logger(__name__).critical(msg)
