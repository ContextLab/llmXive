"""
Logging and error handling infrastructure for the prompt complexity evaluation pipeline.

Provides structured logging, global exception hooks, and safe execution wrappers
to ensure all errors are captured with full context for debugging and audit trails.
"""

import logging
import sys
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Any, Dict

from config import get_project_id, Paths


# Global logger instance (lazy initialization)
_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None


def _get_log_file_path() -> Path:
    """
    Determine the log file path based on project configuration.
    Logs are stored in data/results/logs/ with project-specific naming.
    """
    project_id = get_project_id()
    log_dir = Paths.DATA_RESULTS / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return log_dir / f"{project_id}_{timestamp}.log"


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger instance with structured formatting.

    Args:
        name: Optional logger name. Defaults to the project ID if not provided.

    Returns:
        Configured logging.Logger instance.
    """
    global _logger, _handler

    if _logger is None:
        _logger = logging.getLogger(get_project_id())
        _logger.setLevel(logging.DEBUG)

        # Prevent duplicate handlers if called multiple times
        if not _logger.handlers:
            log_file = _get_log_file_path()

            # File handler for persistent logs
            _handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            _handler.setLevel(logging.DEBUG)

            # Console handler for immediate feedback
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            # Structured formatter
            formatter = logging.Formatter(
                fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            _handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            _logger.addHandler(_handler)
            _logger.addHandler(console_handler)

            _logger.info(f"Logger initialized for project: {get_project_id()}")
            _logger.info(f"Log file: {log_file}")

    if name:
        return _logger.getChild(name)
    return _logger


def setup_structured_logger(name: str = "structured") -> logging.Logger:
    """
    Set up a logger with JSON-structured output for machine parsing.
    Useful for automated analysis of log files.

    Args:
        name: Logger name.

    Returns:
        Logger with JSON formatter.
    """
    logger = get_logger(name)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    log_file = _get_log_file_path()
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "project_id": get_project_id(),
            }
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            if hasattr(record, 'extra_data'):
                log_data.update(record.extra_data)
            return json.dumps(log_data)

    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    return logger


def install_exception_hook() -> None:
    """
    Install a global exception hook to catch and log unhandled exceptions.
    This ensures that even uncaught exceptions are recorded with full stack traces.

    Must be called once at the entry point of the application.
    """
    def exception_handler(exc_type, exc_value, exc_traceback):
        logger = get_logger("global_exception_hook")

        # Skip KeyboardInterrupt (Ctrl+C) as it's expected user behavior
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical(
            "Unhandled exception caught",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

        # Log additional context
        error_context = {
            "error_type": exc_type.__name__,
            "error_message": str(exc_value),
            "project_id": get_project_id(),
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Attempt to write a minimal error report to a separate file
            error_report_path = Paths.DATA_RESULTS / "logs" / "last_crash.json"
            error_report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(error_report_path, 'w', encoding='utf-8') as f:
                json.dump(error_context, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write error report: {e}")

    sys.excepthook = exception_handler


def log_error_context(
    message: str,
    error_type: Optional[str] = None,
    context_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an error with additional contextual information.

    Args:
        message: The error message.
        error_type: Optional type of error (e.g., "ValueError", "Timeout").
        context_data: Optional dictionary of additional context to log.
    """
    logger = get_logger("error_context")

    extra = {}
    if error_type:
        extra["error_type"] = error_type
    if context_data:
        extra.update(context_data)

    # Attach extra data to the record
    class ContextRecord(logging.LogRecord):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.extra_data = extra

    logger.error(message, extra={"extra_data": extra})


def safe_execute(
    func: Callable,
    *args,
    default: Any = None,
    log_on_error: bool = True,
    **kwargs
) -> Any:
    """
    Safely execute a function, catching any exceptions and returning a default value.

    This is useful for operations where failure should not halt the entire pipeline.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        default: Value to return if an exception occurs.
        log_on_error: Whether to log the exception (default: True).
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of func(*args, **kwargs) or the default value on error.
    """
    logger = get_logger("safe_execute")

    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_on_error:
            logger.warning(
                f"Function {func.__name__} failed with {type(e).__name__}: {e}",
                exc_info=True
            )
        return default