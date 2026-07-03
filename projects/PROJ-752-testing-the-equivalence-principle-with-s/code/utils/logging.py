"""
Logging and Error Handling Utilities

Provides standardized logging configuration and custom exception classes
for the llmXive science pipeline.
"""
import logging
import sys
import os
from typing import Optional, Dict, Any
from datetime import datetime

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    pass

class DataUnavailableError(PipelineError):
    """Raised when required data is missing or inaccessible."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid or missing."""
    pass

class AnalysisError(PipelineError):
    """Raised when a scientific analysis step fails."""
    pass


# Logger Registry
_loggers: Dict[str, logging.Logger] = {}


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a logger with standardized configuration.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        Configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    if logger.handlers:
        _loggers[name] = logger
        return logger

    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    _loggers[name] = logger

    return logger


def init_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """
    Initialize logging to both console and optional file.

    Args:
        log_file: Path to log file. If None, only console logging is used.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    )
    root_logger.addHandler(console_handler)

    if log_file:
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        root_logger.addHandler(file_handler)


def log_progress(message: str, logger_name: str = "llmXive") -> None:
    """Log a progress message at INFO level."""
    logger = get_logger(logger_name)
    logger.info(f"[PROGRESS] {message}")


def log_error(message: str, logger_name: str = "llmXive") -> None:
    """Log an error message at ERROR level."""
    logger = get_logger(logger_name)
    logger.error(f"[ERROR] {message}")


def handle_fatal_error(error: Exception, logger_name: str = "llmXive") -> None:
    """
    Handle a fatal error by logging it and exiting the program.

    Args:
        error: The exception that caused the failure.
        logger_name: Name of the logger to use.
    """
    logger = get_logger(logger_name)
    logger.critical(f"FATAL ERROR: {str(error)}")
    logger.critical("Pipeline execution aborted.")
    sys.exit(1)
