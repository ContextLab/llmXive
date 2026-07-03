"""
Logging infrastructure and error handling for the llmXive research pipeline.

Provides a centralized, project-aware logger configuration that:
- Writes to both console and file (rotating)
- Uses project ID from config
- Supports structured JSON logging for downstream parsing
- Integrates with the existing config module
- Implements global error handling hooks to capture uncaught exceptions
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Callable, Any

from config import get_project_id, Paths


# Global logger instance cache
_logger_cache: dict[str, logging.Logger] = {}


def _get_log_directory() -> Path:
    """
    Returns the path to the logs directory within the project structure.
    Creates the directory if it doesn't exist.
    """
    project_id = get_project_id()
    log_dir = Paths.LOGS_DIR / project_id
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates a configured logger for the project.

    Args:
        name: Optional name for the logger. If None, uses the project ID.

    Returns:
        A configured logging.Logger instance.
    """
    project_id = get_project_id()
    logger_name = name if name else project_id

    if logger_name in _logger_cache:
        return _logger_cache[logger_name]

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if logger.handlers:
        _logger_cache[logger_name] = logger
        return logger

    log_dir = _get_log_directory()
    log_file = log_dir / f"{project_id}.log"

    # Formatter for console (human-readable)
    console_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    console_formatter = logging.Formatter(console_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Formatter for file (includes more context)
    file_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        "%(filename)s:%(lineno)d | %(funcName)s | %(message)s"
    )
    file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    _logger_cache[logger_name] = logger
    return logger


def setup_structured_logger(name: str, output_path: Optional[Path] = None) -> logging.Logger:
    """
    Sets up a logger that outputs JSON-structured logs for pipeline analysis.

    Args:
        name: Logger name.
        output_path: Optional custom path for structured logs. Defaults to
                     data/processed/structured_logs.jsonl.

    Returns:
        A configured logger with JSON formatting.
    """
    import json
    from datetime import datetime

    logger = logging.getLogger(f"structured.{name}")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    if output_path is None:
        output_path = Paths.PROCESSED_DATA_DIR / "structured_logs.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_data = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            # Add extra fields if present
            if hasattr(record, "extra_data"):
                log_data["extra"] = record.extra_data
            return json.dumps(log_data)

    file_handler = logging.FileHandler(output_path, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())

    logger.addHandler(file_handler)
    return logger


# --- Error Handling Infrastructure ---

def _uncaught_exception_handler(exctype: type, value: Exception, tb: Any) -> None:
    """
    Global exception handler to log uncaught exceptions before the program crashes.
    This ensures critical errors are persisted to the log file even if not caught locally.
    """
    logger = get_logger("system")
    logger.critical(
        "Uncaught exception: %s\n%s",
        value,
        "".join(traceback.format_exception(exctype, value, tb))
    )
    # Call the original handler to ensure standard behavior (print to stderr)
    sys.__excepthook__(exctype, value, tb)


def install_exception_hook() -> None:
    """
    Installs the global uncaught exception handler.
    Should be called once at the entry point of the application (e.g., main.py).
    """
    sys.excepthook = _uncaught_exception_handler


def log_error_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict] = None,
    level: int = logging.ERROR
) -> None:
    """
    Logs an error with additional context information.

    Args:
        logger: The logger instance to use.
        error: The exception to log.
        context: Optional dictionary of contextual data (e.g., problem_id, variant_label).
        level: Logging level (default ERROR).
    """
    message = str(error)
    if context:
        message += f" | Context: {context}"

    logger.log(level, message, extra={"extra_data": context} if context else {})


def safe_execute(
    func: Callable,
    *args: Any,
    logger_name: Optional[str] = None,
    default_return: Any = None,
    **kwargs: Any
) -> Any:
    """
    Executes a function with automatic error logging and optional default return.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        logger_name: Optional name for the logger. If None, uses project ID.
        default_return: Value to return if an exception occurs.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of func, or default_return if an exception is caught.
    """
    logger = get_logger(logger_name)
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_error_context(logger, e, context={"function": func.__name__})
        return default_return


# Re-export standard logging levels for convenience
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL