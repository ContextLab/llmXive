"""
Logging module for the Equivalence Principle Testing Pipeline.

Provides centralized logging configuration, custom exceptions, and
utility functions for consistent logging across the project.
"""

import logging
import sys
import os
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import traceback


# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    pass


class DataUnavailableError(PipelineError):
    """Raised when required data is missing or inaccessible."""
    pass


class ConfigurationError(PipelineError):
    """Raised when configuration is invalid or missing required fields."""
    pass


class AnalysisError(PipelineError):
    """Raised when an analysis step fails."""
    pass


class ModelConvergenceError(AnalysisError):
    """Raised when a model fails to converge."""
    pass


class ValidationError(AnalysisError):
    """Raised when validation checks fail."""
    pass


class ModelError(AnalysisError):
    """Raised when a model encounters an internal error."""
    pass


# Global logger registry
_loggers: Dict[str, logging.Logger] = {}
_initialized = False


def init_logging(
    log_file: Optional[str] = None,
    log_level: int = logging.INFO,
    console: bool = True,
    project_root: Optional[str] = None
) -> None:
    """
    Initialize the logging configuration for the entire project.

    Args:
        log_file: Path to the log file. If None, only console logging is configured.
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console: Whether to log to console.
        project_root: Base directory for relative log file paths. If None, uses current dir.
    """
    global _initialized

    if _initialized:
        return

    # Determine project root
    if project_root is None:
        # Default to code/ directory relative to current working directory
        # or try to find the project root
        current_dir = os.getcwd()
        # Look for project root markers
        for marker in ['.git', 'requirements.txt', 'tasks.md']:
            if os.path.exists(os.path.join(current_dir, marker)):
                project_root = current_dir
                break
        else:
            project_root = current_dir

    # Create log directory if needed
    log_dir = os.path.join(project_root, 'data', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        # Handle relative paths
        if not os.path.isabs(log_file):
            log_file = os.path.join(project_root, log_file)

        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the specified name.

    Args:
        name: Logger name (typically module name).

    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    _loggers[name] = logger
    return logger


def log_progress(
    logger: logging.Logger,
    step_name: str,
    message: str,
    level: int = logging.INFO,
    **kwargs: Any
) -> None:
    """
    Log a progress message with structured context.

    Args:
        logger: Logger instance.
        step_name: Name of the current step.
        message: Progress message.
        level: Logging level.
        **kwargs: Additional context to include.
    """
    context_str = ', '.join(f'{k}={v}' for k, v in kwargs.items()) if kwargs else ''
    full_message = f"[{step_name}] {message}"
    if context_str:
        full_message += f" ({context_str})"
    logger.log(level, full_message)


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[str] = None
) -> None:
    """
    Log an error with full traceback and optional context.

    Args:
        logger: Logger instance.
        error: Exception to log.
        context: Optional context string.
    """
    error_msg = f"{type(error).__name__}: {str(error)}"
    if context:
        error_msg = f"{context}: {error_msg}"

    logger.error(error_msg)
    logger.debug(traceback.format_exc())


def handle_fatal_error(
    logger: logging.Logger,
    error: Exception,
    step_name: str,
    exit_code: int = 1
) -> None:
    """
    Handle a fatal error by logging and exiting.

    Args:
        logger: Logger instance.
        error: Fatal exception.
        step_name: Name of the step where error occurred.
        exit_code: Exit code for the process.
    """
    log_error(logger, error, f"FATAL ERROR in {step_name}")
    logger.error(f"Pipeline failed at step: {step_name}")
    sys.exit(exit_code)


def log_step_duration(
    logger: logging.Logger,
    step_name: str,
    start_time: datetime,
    end_time: Optional[datetime] = None
) -> float:
    """
    Log the duration of a step.

    Args:
        logger: Logger instance.
        step_name: Name of the step.
        start_time: Start datetime.
        end_time: End datetime (defaults to now).

    Returns:
        Duration in seconds.
    """
    if end_time is None:
        end_time = datetime.now()

    duration = (end_time - start_time).total_seconds()
    logger.info(f"[{step_name}] Completed in {duration:.2f} seconds")
    return duration


class TimedStep:
    """Context manager for timing and logging a step."""

    def __init__(
        self,
        logger: logging.Logger,
        step_name: str,
        log_duration: bool = True
    ):
        self.logger = logger
        self.step_name = step_name
        self.log_duration = log_duration
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def __enter__(self) -> 'TimedStep':
        self.start_time = datetime.now()
        self.logger.info(f"[{self.step_name}] Starting...")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.end_time = datetime.now()
        if exc_type is not None:
            self.logger.error(f"[{self.step_name}] Failed with {exc_type.__name__}: {exc_val}")
        elif self.log_duration:
            duration = (self.end_time - self.start_time).total_seconds()
            self.logger.info(f"[{self.step_name}] Completed in {duration:.2f} seconds")


def track_step(
    logger: logging.Logger,
    step_name: str,
    func: Callable
) -> Callable:
    """
    Decorator to track step execution time and status.

    Args:
        logger: Logger instance.
        step_name: Name of the step.
        func: Function to wrap.

    Returns:
        Wrapped function.
    """
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            logger.info(f"[{step_name}] Starting...")
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"[{step_name}] Completed in {duration:.2f} seconds")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"[{step_name}] Failed after {duration:.2f} seconds: {type(e).__name__}: {e}")
            raise

    return wrapper


# Initialize logging with defaults when module is imported
# This can be overridden by calling init_logging() explicitly
try:
    init_logging(
        log_file='data/logs/pipeline.log',
        log_level=logging.INFO,
        console=True
    )
except Exception:
    # Silently fail during import; user must call init_logging() explicitly
    pass