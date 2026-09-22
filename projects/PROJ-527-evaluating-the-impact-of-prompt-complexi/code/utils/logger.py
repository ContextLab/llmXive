"""
Logging and error handling infrastructure for the prompt complexity evaluation pipeline.

Provides structured logging, exception hooks, and safe execution wrappers.
"""
import logging
import sys
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Callable, Dict
from config import Paths, get_project_id


# Global logger instance cache
_loggers: Dict[str, logging.Logger] = {}
_exception_hook_installed = False


def _get_log_file_path() -> Path:
    """Determine the log file path based on project configuration."""
    project_id = get_project_id()
    log_dir = Path(Paths.LOGS)
    log_dir.mkdir(parents=True, exist_ok=True)
    # Use a timestamped log file to avoid concurrency issues
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"{project_id}_{timestamp}.log"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a named logger with project-specific configuration.
    
    Args:
        name: Optional name for the logger. If None, uses the module name.
        
    Returns:
        Configured logging.Logger instance.
    """
    if name is None:
        # Default to module name if not provided
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get("__name__", "unknown")
        else:
            name = "unknown"
    
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers multiple times
    if not logger.handlers:
        # File handler
        log_file = _get_log_file_path()
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter with structured JSON-like output for files
        file_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s", '
            '"module": "%(module)s", "function": "%(funcName)s", '
            '"line": %(lineno)d}',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Simple formatter for console
        console_formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    _loggers[name] = logger
    return logger


def setup_structured_logger() -> logging.Logger:
    """
    Setup a primary logger for the pipeline execution with JSON formatting.
    
    Returns:
        Configured logger instance.
    """
    logger = get_logger("pipeline")
    logger.info("Pipeline logging initialized.")
    return logger


def install_exception_hook() -> None:
    """
    Install a global exception hook to log uncaught exceptions.
    
    This ensures that any unhandled exception is logged with full traceback
    before the program terminates.
    """
    global _exception_hook_installed
    if _exception_hook_installed:
        return
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        logger = get_logger("uncaught_exception")
        if issubclass(exc_type, KeyboardInterrupt):
            # User interrupted, don't log as error
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"Uncaught exception: {exc_type.__name__}: {exc_value}"
        logger.critical(error_msg)
        logger.critical("Traceback:\n%s", "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        
        # Also write to a specific error file for quick access
        error_file = Path(Paths.LOGS) / "last_error.log"
        error_file.parent.mkdir(parents=True, exist_ok=True)
        with open(error_file, 'w', encoding='utf-8') as f:
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Exception: {error_msg}\n")
            f.write("Traceback:\n")
            f.writelines(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = exception_handler
    _exception_hook_installed = True
    get_logger("pipeline").info("Global exception hook installed.")


def log_error_context(
    error: Exception,
    context: Dict[str, Any],
    logger_name: Optional[str] = None
) -> None:
    """
    Log an error with additional contextual information.
    
    Args:
        error: The exception instance.
        context: A dictionary of contextual key-value pairs (e.g., problem_id, variant).
        logger_name: Optional logger name. Defaults to "error_context".
    """
    logger = get_logger(logger_name or "error_context")
    
    error_details = {
        "type": error.__class__.__name__,
        "message": str(error),
        "context": context,
        "traceback": traceback.format_exc()
    }
    
    logger.error(
        "Error occurred: %s | Context: %s",
        error_details["type"],
        json.dumps(context, default=str)
    )
    logger.debug("Full error details:\n%s", json.dumps(error_details, indent=2, default=str))


def safe_execute(
    func: Callable,
    *args,
    on_error: Optional[Callable[[Exception, Dict[str, Any]], None]] = None,
    default: Optional[Any] = None,
    **kwargs
) -> Any:
    """
    Safely execute a function, catching exceptions and logging them.
    
    Args:
        func: The function to execute.
        *args: Positional arguments to pass to func.
        on_error: Optional callback to handle the error (receives exception and context).
        default: Value to return if an exception occurs and on_error is not provided.
        **kwargs: Keyword arguments to pass to func.
        
    Returns:
        The result of func, or the default value if an error occurs.
    """
    logger = get_logger("safe_execute")
    context = {
        "function": func.__name__,
        "args": str(args),
        "kwargs": str(kwargs)
    }
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error_context(e, context, logger.name)
        if on_error:
            on_error(e, context)
            return None
        else:
            logger.warning("Returning default value due to error.")
            return default