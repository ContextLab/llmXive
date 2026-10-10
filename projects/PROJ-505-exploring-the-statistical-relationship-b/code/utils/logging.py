"""
Logging and error handling utilities.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from datetime import datetime
import time
import resource

class PipelineError(Exception):
    """Base class for pipeline‑wide errors."""
    pass

class DataIngestionError(PipelineError):
    """Raised when data ingestion fails."""
    pass

class AlignmentError(PipelineError):
    """Raised during temporal alignment problems."""
    pass

class AnalysisError(PipelineError):
    """Raised for analysis‑stage failures."""
    pass

class ConfigError(PipelineError):
    """Raised for configuration‑related issues."""
    pass

class ValidationError(PipelineError):
    """Raised when validation of inputs/outputs fails."""
    pass

def get_logger(name: str) -> logging.Logger:
    """
    Return a logger with a simple console handler.
    If the logger has no handlers yet, a StreamHandler to stdout is attached.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# Create a module‑level logger as required by the specification.
# This logger is instantiated at import time and will have at least the
# console handler configured by ``get_logger``.
logger = get_logger(__name__)

def setup_logging(log_file: Optional[Path] = None) -> None:
    """
    Configure file logging in addition to the default console logger.
    If ``log_file`` is provided, a FileHandler is added to the root logger.
    """
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logging.root.addHandler(handler)

def log_duration(func):
    """
    Decorator that logs the execution time of ``func`` at INFO level.
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger = get_logger(func.__module__)
        logger.info(f"{func.__name__} completed in {end - start:.2f} seconds")
        return result
    return wrapper

def check_memory_usage() -> float:
    """Check current memory usage in GB."""
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # On Linux, ru_maxrss is in KB; on macOS, it's in bytes
    if sys.platform == "darwin":
        usage_gb = usage / (1024 ** 3)
    else:
        usage_gb = usage / (1024 * 1024)
    return usage_gb

def log_error_and_raise(error_type: type, message: str) -> None:
    """Log an error message and raise the specified ``error_type``."""
    logger = get_logger(__name__)
    logger.error(message)
    raise error_type(message)

def safe_execute(func, *args, **kwargs):
    """
    Execute ``func`` safely, returning a tuple ``(result, None)`` on success
    or ``(None, exception)`` on failure.
    """
    try:
        return func(*args, **kwargs), None
    except Exception as e:
        return None, e