import logging
import sys
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any
from contextlib import contextmanager
import threading

# Global logger registry to ensure consistency across modules
_logger_registry: Dict[str, logging.Logger] = {}
_default_log_level = logging.INFO
_log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
_date_format = "%Y-%m-%d %H:%M:%S"

class LogContext:
    """Context manager for adding contextual information to log records."""
    
    def __init__(self, logger: logging.Logger, **context: Any):
        self.logger = logger
        self.context = context
        self.old_factory = None
    
    def __enter__(self):
        self.old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record
        
        logging.setLogRecordFactory(record_factory)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)
        return False

def setup_logging(
    log_level: Optional[int] = None,
    log_file: Optional[Union[str, Path]] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = False
) -> logging.Logger:
    """
    Configure the root logger with console and/or file handlers.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Path to log file. If None, no file handler is created.
        log_format: Format string for log messages.
        date_format: Date format string for timestamps.
        enable_console: Whether to add a console handler.
        enable_file: Whether to add a file handler (requires log_file).
    
    Returns:
        The root logger instance.
    """
    global _default_log_level, _log_format, _date_format
    
    if log_level is not None:
        _default_log_level = log_level
    if log_format is not None:
        _log_format = log_format
    if date_format is not None:
        _date_format = date_format
    
    root_logger = logging.getLogger()
    root_logger.setLevel(_default_log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    formatter = logging.Formatter(_log_format, date_format)
    
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_default_log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    if enable_file and log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(_default_log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_module_logger(module_name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger for a specific module, ensuring it's configured consistently.
    
    Args:
        module_name: Optional module name. If None, uses the caller's module name.
    
    Returns:
        Configured logger instance.
    """
    global _default_log_level
    
    if module_name is None:
        # Get the caller's module name
        frame = sys._getframe(1)
        module_name = frame.f_globals.get("__name__", "unknown")
    
    if module_name in _logger_registry:
        return _logger_registry[module_name]
    
    logger = logging.getLogger(module_name)
    logger.setLevel(_default_log_level)
    
    # If no handlers exist, add default ones (in case setup_logging wasn't called)
    if not logger.handlers:
        formatter = logging.Formatter(_log_format, date_format=_date_format)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(_default_log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    _logger_registry[module_name] = logger
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Convenience function to get a logger, alias for get_module_logger.
    
    Args:
        name: Optional logger name.
    
    Returns:
        Configured logger instance.
    """
    return get_module_logger(name)

@contextmanager
def log_context(logger: logging.Logger, **context: Any):
    """
    Context manager to add contextual information to log records within a block.
    
    Args:
        logger: The logger to use.
        **context: Key-value pairs to add to log records.
    
    Usage:
        with log_context(logger, user_id=123, action="fetch"):
            logger.info("Processing data")
        # Logs will include user_id=123 and action=fetch
    """
    ctx = LogContext(logger, **context)
    with ctx:
        yield

def handle_exception(
    logger: logging.Logger,
    exception: Exception,
    message: Optional[str] = None,
    log_level: int = logging.ERROR,
    reraise: bool = False
) -> None:
    """
    Log an exception with context and optionally re-raise it.
    
    Args:
        logger: Logger instance to use.
        exception: The exception to log.
        message: Optional custom message to log.
        log_level: Logging level for the exception (default: ERROR).
        reraise: Whether to re-raise the exception after logging.
    
    Raises:
        The original exception if reraise=True.
    """
    if message:
        logger.log(log_level, f"{message}: {type(exception).__name__}: {str(exception)}")
    else:
        logger.log(log_level, f"{type(exception).__name__}: {str(exception)}")
    
    # Log traceback for debugging
    import traceback
    logger.log(log_level, traceback.format_exc())
    
    if reraise:
        raise exception

def configure_thread_specific_logging(
    thread_name: Optional[str] = None,
    log_level: Optional[int] = None
) -> logging.Logger:
    """
    Configure logging for a specific thread with optional thread name in logs.
    
    Args:
        thread_name: Optional thread name to include in log format.
        log_level: Optional log level override for this thread.
    
    Returns:
        Logger configured for this thread.
    """
    if thread_name is None:
        thread_name = threading.current_thread().name
    
    logger = get_module_logger(f"{thread_name}")
    
    if log_level is not None:
        logger.setLevel(log_level)
    
    # Add thread name to formatter if not already present
    existing_handlers = logger.handlers.copy()
    for handler in existing_handlers:
        if isinstance(handler, logging.StreamHandler):
            # Check if thread info is already in formatter
            current_format = handler.formatter._fmt if hasattr(handler.formatter, '_fmt') else ""
            if "%(threadName)s" not in current_format:
                new_format = f"%(threadName)s - {current_format}"
                handler.setFormatter(logging.Formatter(new_format, date_format=_date_format))
    
    return logger

# Initialize root logger with default settings if not already done
if not logging.getLogger().handlers:
    setup_logging()