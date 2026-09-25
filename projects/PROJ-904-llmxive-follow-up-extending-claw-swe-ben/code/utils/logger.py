"""
Logging and Error Handling Utilities.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional
from datetime import datetime

class ResearchError(Exception):
    """Base class for research errors."""
    pass

class DataLoadError(ResearchError):
    """Error during data loading."""
    pass

class ModelExecutionError(ResearchError):
    """Error during model execution."""
    pass

class ConfigurationError(ResearchError):
    """Error in configuration."""
    pass

class AnalysisError(ResearchError):
    """Error during analysis."""
    pass

def setup_logger(name: str = "llmxive", level: int = logging.INFO) -> logging.Logger:
    """
    Sets up a logger with file and console handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        fh = logging.FileHandler(log_dir / f"{name}.log")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def log_error(exception: Exception, context: str = ""):
    """
    Logs an error with full traceback.
    """
    logger = logging.getLogger("llmxive")
    error_msg = f"{context}: {str(exception)}\n{traceback.format_exc()}"
    logger.error(error_msg)

def safe_execute(func, *args, **kwargs):
    """
    Executes a function and catches exceptions, logging them.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error(e, f"Error in {func.__name__}")
        return None
