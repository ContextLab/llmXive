"""
logging_config.py

Sets up logging infrastructure for reproducible audit trails.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from config import load_config

# Global logger instance
_logger = None

def setup_logger(name: str, log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configures a logger with console and optional file output.
    """
    global _logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if already configured
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a logger instance, creating it if necessary.
    """
    global _logger
    if _logger is None:
        # Default setup if not explicitly configured
        _logger = setup_logger(name)
    return logging.getLogger(name)

def info(logger, msg):
    logger.info(msg)

def debug(logger, msg):
    logger.debug(msg)

def warning(logger, msg):
    logger.warning(msg)

def error(logger, msg, exc_info=False):
    logger.error(msg, exc_info=exc_info)

def critical(logger, msg):
    logger.critical(msg)
