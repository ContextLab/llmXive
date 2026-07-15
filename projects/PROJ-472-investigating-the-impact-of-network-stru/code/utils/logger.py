import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_data_root

class ResearchError(Exception):
    """Base exception for research pipeline errors."""
    pass

class DataLoadError(ResearchError):
    """Error raised when data loading fails."""
    pass

class SimulationError(ResearchError):
    """Error raised when simulation fails."""
    pass

class AnalysisError(ResearchError):
    """Error raised when analysis fails."""
    pass

class ConfigError(ResearchError):
    """Error raised when configuration is invalid."""
    pass

class StructuredErrorFilter(logging.Filter):
    """Filter to structure error logs consistently."""
    def filter(self, record):
        if record.levelno >= logging.ERROR:
            record.msg = f"[{record.name}] {record.msg}"
        return True

_loggers: Dict[str, logging.Logger] = {}

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name (usually __name__).
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Create handlers
    log_dir = get_data_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_handler = logging.FileHandler(log_dir / f"pipeline_{timestamp}.log")
    console_handler = logging.StreamHandler(sys.stdout)

    # Set levels
    file_handler.setLevel(level)
    console_handler.setLevel(level)

    # Set formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add filter
    file_handler.addFilter(StructuredErrorFilter())
    console_handler.addFilter(StructuredErrorFilter())

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger by name."""
    if name not in _loggers:
        return setup_logger(name)
    return _loggers[name]

def get_traceback_info(exc: Exception) -> str:
    """Get formatted traceback information."""
    return ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))

def log_exception(logger: logging.Logger, exc: Exception, msg: str = "An error occurred"):
    """Log an exception with full traceback."""
    logger.error(f"{msg}: {str(exc)}")
    logger.debug(get_traceback_info(exc))

def log_pipeline_start(logger: logging.Logger, pipeline_name: str, subject_id: Optional[str] = None):
    """Log the start of a pipeline or subject processing."""
    context = f"Subject: {subject_id}" if subject_id else "Global"
    logger.info(f"--- STARTING {pipeline_name} [{context}] ---")

def log_pipeline_end(logger: logging.Logger, pipeline_name: str, subject_id: Optional[str] = None):
    """Log the end of a pipeline or subject processing."""
    context = f"Subject: {subject_id}" if subject_id else "Global"
    logger.info(f"--- COMPLETED {pipeline_name} [{context}] ---")

def handle_exceptions(func):
    """Decorator to handle exceptions in pipeline functions."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        try:
            return func(*args, **kwargs)
        except ResearchError:
            raise
        except Exception as e:
            log_exception(logger, e, f"Unexpected error in {func.__name__}")
            raise SimulationError(f"Pipeline failed: {str(e)}") from e
    return wrapper

def safe_execute(func, *args, **kwargs):
    """Safely execute a function and return result or None on error."""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger = get_logger(func.__module__)
        log_exception(logger, e)
        return None
