import logging
import sys
import os
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import traceback

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when required data cannot be fetched or is missing."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid or missing."""
    pass

class AnalysisError(PipelineError):
    """Raised when analysis steps fail."""
    pass

class ModelConvergenceError(AnalysisError):
    """Raised when an optimization model fails to converge."""
    pass

class ValidationError(AnalysisError):
    """Raised when validation checks fail."""
    pass

class ModelError(AnalysisError):
    """Raised when a physical model calculation fails."""
    pass

_logger: Optional[logging.Logger] = None

def init_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize the global logger with console and optional file handlers.
    """
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("llmXive_pipeline")
    _logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    _logger.addHandler(ch)

    # File Handler (if specified)
    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        _logger.addHandler(fh)

    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get the global logger or a child logger."""
    if _logger is None:
        init_logging()
    if name:
        return _logger.getChild(name)
    return _logger

def log_progress(message: str, level: str = "INFO"):
    """Log a progress message."""
    logger = get_logger()
    getattr(logger, level.lower())(message)

def log_error(message: str, error: Optional[Exception] = None):
    """Log an error message, optionally with traceback."""
    logger = get_logger()
    logger.error(message)
    if error:
        logger.error(traceback.format_exc())

def handle_fatal_error(message: str, error: Exception):
    """Log a fatal error and exit."""
    logger = get_logger()
    logger.critical(f"FATAL: {message}")
    logger.critical(traceback.format_exc())
    sys.exit(1)

def log_step_duration(step_name: str, duration_seconds: float):
    """Log the duration of a step."""
    logger = get_logger()
    logger.info(f"Step '{step_name}' completed in {duration_seconds:.2f}s")

class TimedStep:
    """Context manager to track step duration."""
    def __init__(self, step_name: str):
        self.step_name = step_name
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            log_step_duration(self.step_name, duration)
