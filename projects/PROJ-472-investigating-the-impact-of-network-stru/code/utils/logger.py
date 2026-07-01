import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
from dataclasses import dataclass

# -----------------------------------------------------------------------------
# Custom Exception Hierarchy
# -----------------------------------------------------------------------------

class ResearchError(Exception):
    """Base exception for all research pipeline errors."""
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

class DataLoadError(ResearchError):
    """Raised when data loading or parsing fails."""
    pass

class SimulationError(ResearchError):
    """Raised when simulation steps fail (e.g., Wilson-Cowan convergence)."""
    pass

class AnalysisError(ResearchError):
    """Raised when analysis or metric computation fails."""
    pass

class ConfigError(ResearchError):
    """Raised when configuration loading or validation fails."""
    pass

# -----------------------------------------------------------------------------
# Structured Logging Filter
# -----------------------------------------------------------------------------

class StructuredErrorFilter(logging.Filter):
    """
    A filter that attaches structured context to error records.
    Ensures that exception details are consistently formatted for downstream parsing.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno >= logging.ERROR:
            # Attach exception info if present
            if record.exc_info:
                exc_type, exc_value, exc_tb = record.exc_info
                record.exc_text = traceback.format_exception(*record.exc_info)
                # Attach custom context if available in the record dict
                if hasattr(record, 'context'):
                    record.context_json = json.dumps(record.context)
            else:
                record.exc_text = None
        return True

# -----------------------------------------------------------------------------
# Logger Setup
# -----------------------------------------------------------------------------

_loggers: Dict[str, logging.Logger] = {}

def setup_logger(
    name: str = "llmXive",
    log_file: Optional[Path] = None,
    level: Optional[str] = None,
    include_console: bool = True
) -> logging.Logger:
    """
    Configures and returns a logger with file and console handlers.
    
    Args:
        name: Logger name.
        log_file: Optional path to a log file. If None, logs to a default location
                 under data/logs if the directory exists, else skips file logging.
        level: Log level string (e.g., 'INFO', 'DEBUG'). Defaults to env var or 'INFO'.
        include_console: Whether to add a console handler.
    
    Returns:
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to allow lower-level handlers to filter
    logger.handlers.clear()  # Prevent duplicate handlers in interactive sessions

    # Determine level
    if level:
        log_level = getattr(logging, level.upper(), logging.INFO)
    else:
        env_level = os.getenv("LOG_LEVEL", "INFO")
        log_level = getattr(logging, env_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler
    if log_file is None:
        # Try to find default log directory
        default_log_dir = Path("data") / "logs"
        if default_log_dir.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = default_log_dir / f"{name}_{timestamp}.log"
            default_log_dir.mkdir(parents=True, exist_ok=True)
        else:
            log_file = None

    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            file_handler.addFilter(StructuredErrorFilter())
            logger.addHandler(file_handler)
        except IOError as e:
            # Fallback if file cannot be opened
            print(f"Warning: Could not open log file {log_file}: {e}", file=sys.stderr)

    # Console Handler
    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(StructuredErrorFilter())
        logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves an existing logger or creates a new one with default settings.
    """
    if name not in _loggers:
        # Default setup if not explicitly configured yet
        return setup_logger(name)
    return _loggers[name]

def get_traceback_info(exc_info: tuple) -> str:
    """
    Formats exception info into a readable string.
    """
    return "".join(traceback.format_exception(*exc_info))

def log_exception(
    logger: logging.Logger,
    exc: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: int = logging.ERROR
) -> None:
    """
    Logs an exception with detailed traceback and optional context.
    """
    extra = {"context": context} if context else {}
    logger.log(level, f"Exception occurred: {str(exc)}", exc_info=True, extra=extra)

def log_pipeline_start(logger: logging.Logger, pipeline_name: str, params: Optional[Dict] = None) -> None:
    """Logs the start of a pipeline run."""
    msg = f"Pipeline '{pipeline_name}' starting."
    if params:
        msg += f" Parameters: {json.dumps(params)}"
    logger.info(msg)

def log_pipeline_end(logger: logging.Logger, pipeline_name: str, success: bool) -> None:
    """Logs the end of a pipeline run."""
    status = "completed successfully" if success else "failed"
    logger.info(f"Pipeline '{pipeline_name}' {status}.")

# -----------------------------------------------------------------------------
# Decorators & Context Managers for Error Handling
# -----------------------------------------------------------------------------

def handle_exceptions(logger: Optional[logging.Logger] = None, custom_exception: Optional[type] = None):
    """
    Decorator to wrap a function in try/except, logging errors and raising a custom exception.
    
    Args:
        logger: Logger instance. If None, uses 'llmXive'.
        custom_exception: Exception class to raise on failure. Defaults to ResearchError.
    """
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            local_logger = logger or get_logger()
            exc_type = custom_exception or ResearchError
            
            try:
                return func(*args, **kwargs)
            except exc_type as e:
                # Re-raise custom exceptions after logging
                log_exception(local_logger, e, context={"function": func.__name__})
                raise
            except Exception as e:
                # Wrap unexpected exceptions
                local_logger.critical(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
                raise exc_type(f"Unexpected error in {func.__name__}: {str(e)}")
        return wrapper
    return decorator

def safe_execute(func, *args, default=None, logger: Optional[logging.Logger] = None, **kwargs):
    """
    Executes a function and returns the default value on any exception, logging the error.
    """
    local_logger = logger or get_logger()
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_exception(local_logger, e, context={"function": func.__name__})
        return default