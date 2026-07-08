import logging
import sys
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any
from contextlib import contextmanager
import traceback
import threading

# Global logger registry to ensure consistent configuration across threads
_logger_registry: Dict[str, logging.Logger] = {}
_lock = threading.Lock()

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log levels mapping
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class LogContext:
    """
    Context object to carry logging context (e.g., window_id, step_name)
    through the application.
    """
    def __init__(self, **kwargs: Any):
        self.context = kwargs

    def __str__(self) -> str:
        return ", ".join(f"{k}={v}" for k, v in self.context.items())


def setup_logging(
    level: Union[str, int] = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    format_str: Optional[str] = None,
    date_format: Optional[str] = None,
) -> None:
    """
    Configure the root logger and ensure consistent logging behavior.

    Args:
        level: Log level (string name or integer constant).
        log_file: Optional path to a log file. If None, logs to stderr.
        format_str: Optional custom log format string.
        date_format: Optional custom date format string.
    """
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)

    fmt = format_str or DEFAULT_FORMAT
    date_fmt = date_format or DEFAULT_DATE_FORMAT

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(fmt, date_fmt)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        root_logger.addHandler(file_handler)

    # Prevent propagation to root if this is the root logger setup
    # (Usually not needed if we are setting root, but good practice for sub-loggers)
    root_logger.propagate = False


def get_module_logger(module_name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger for a specific module.
    If module_name is None, attempts to infer from the caller's stack frame.

    Args:
        module_name: Optional explicit module name.

    Returns:
        Configured logging.Logger instance.
    """
    if module_name is None:
        # Infer from caller
        frame = sys._getframe(1)
        module_name = frame.f_globals.get("__name__", "root")

    with _lock:
        if module_name not in _logger_registry:
            logger = logging.getLogger(module_name)
            # Ensure logger inherits root configuration but doesn't propagate
            # if root was explicitly configured to avoid double logging
            if not logger.handlers:
                # Copy handlers from root if it has any
                root = logging.getLogger()
                for handler in root.handlers:
                    logger.addHandler(handler)
            logger.setLevel(root_logger.level if (root_logger := logging.getLogger()) else logging.INFO)
            _logger_registry[module_name] = logger
        return _logger_registry[module_name]


# Alias for get_module_logger to match API surface
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience wrapper for get_module_logger.

    Args:
        name: Logger name (module name).

    Returns:
        Configured logging.Logger instance.
    """
    return get_module_logger(name)


@contextmanager
def log_context(logger: Optional[logging.Logger] = None, **context_kwargs: Any):
    """
    Context manager to log entry and exit of a block, optionally with context data.

    Usage:
        with log_context("Processing window"):
            ...

    Args:
        logger: Logger instance. If None, uses the module logger of the caller.
        **context_kwargs: Key-value pairs to include in the log message.
    """
    if logger is None:
        logger = get_module_logger()

    ctx_str = ""
    if context_kwargs:
        ctx_str = f" [{LogContext(**context_kwargs)}]"

    logger.info(f"Entering context{ctx_str}")
    try:
        yield
    except Exception as e:
        logger.error(f"Error in context{ctx_str}: {e}", exc_info=True)
        raise
    finally:
        logger.info(f"Exiting context{ctx_str}")


def handle_exception(
    logger: Optional[logging.Logger] = None,
    message: Optional[str] = None,
    reraise: bool = False,
) -> None:
    """
    Log the current exception with full traceback.

    Args:
        logger: Logger instance. If None, uses the module logger of the caller.
        message: Optional custom message to prepend.
        reraise: If True, re-raises the exception after logging.
    """
    if logger is None:
        logger = get_module_logger()

    exc_type, exc_value, exc_tb = sys.exc_info()
    if exc_type is None:
        logger.warning("handle_exception called but no active exception.")
        return

    error_msg = f"{message}: {exc_value}" if message else str(exc_value)
    logger.error(error_msg, exc_info=(exc_type, exc_value, exc_tb))

    if reraise:
        raise exc_value.with_traceback(exc_tb)


def configure_thread_specific_logging(
    thread_name: str,
    level: Union[str, int] = "INFO",
    log_file: Optional[Union[str, Path]] = None,
) -> None:
    """
    Configure logging specifically for a thread context.
    This is a wrapper that ensures the root logger is configured appropriately
    for the thread if needed, though Python's logging module is thread-safe by default.
    This function is primarily for explicit setup in multi-threaded entry points.

    Args:
        thread_name: Name of the thread.
        level: Log level.
        log_file: Optional log file path.
    """
    # Python logging is thread-safe. We just ensure global config is set.
    # If thread-specific files are needed, they should be handled by the caller
    # passing specific log_file paths.
    setup_logging(level=level, log_file=log_file)
    logger = get_module_logger(f"thread_{thread_name}")
    logger.info(f"Logging configured for thread: {thread_name}")

# Initialize root logger configuration if not already done
# This ensures that if this module is imported first, logging is ready.
if not logging.getLogger().handlers:
    setup_logging()