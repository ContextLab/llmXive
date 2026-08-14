"""
Legacy/Compatibility logger module.
Provides simple initialization functions that delegate to logging_config.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from .logging_config import setup_logging, get_logger

def init_project_logger() -> logging.Logger:
    """
    Initialize the project logging infrastructure and return the root logger.
    """
    return setup_logging() or get_logger("solder_pipeline")

def create_module_logger(module_name: str) -> logging.Logger:
    """
    Create and return a logger for a specific module.
    
    Args:
        module_name: The name of the module (e.g., 'ingestion.aggregator').
        
    Returns:
        A configured Logger instance.
    """
    return get_logger(module_name)

def log(message: str, level: str = "info") -> None:
    """
    Simple logging function for quick debug statements.
    
    Args:
        message: The message to log.
        level: The log level string ('debug', 'info', 'warning', 'error', 'critical').
    """
    logger = get_logger("utils.logger")
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    log_level = level_map.get(level.lower(), logging.INFO)
    logger.log(log_level, message)
