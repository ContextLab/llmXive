import json
import logging
import os
import sys
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, Optional

class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs structured JSON logs.
    Includes timestamp, level, logger name, message, and optional context.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "traceback": "".join(
                    traceback.format_exception(*record.exc_info)
                ),
            }

        if hasattr(record, "context"):
            log_data["context"] = record.context

        if record.module:
            log_data["module"] = record.module
            log_data["lineno"] = record.lineno

        return json.dumps(log_data, ensure_ascii=False)


class ErrorTracker:
    """
    Tracks errors encountered during execution for audit and debugging purposes.
    Stores errors in a list and can write them to a file.
    """

    def __init__(self):
        self.errors: list[Dict[str, Any]] = []
        self._lock = None  # Thread safety handled by caller or external lock if needed

    def record(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Record an error with optional context."""
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": type(error).__name__,
            "message": str(error),
            "traceback": "".join(traceback.format_exception(type(error), error, error.__traceback__)),
        }
        if context:
            error_entry["context"] = context
        self.errors.append(error_entry)

    def get_errors(self) -> list[Dict[str, Any]]:
        """Return the list of recorded errors."""
        return self.errors.copy()

    def write_to_file(self, filepath: str) -> None:
        """Write all recorded errors to a JSON file."""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.errors, f, indent=2, ensure_ascii=False)

    def clear(self) -> None:
        """Clear the error log."""
        self.errors.clear()


_global_tracker: Optional[ErrorTracker] = None
_logger: Optional[logging.Logger] = None


def create_error_tracker() -> ErrorTracker:
    """Factory function to create a new ErrorTracker instance."""
    return ErrorTracker()


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    enable_console: bool = True
) -> logging.Logger:
    """
    Configure the root logger with JSON formatting and optional file/console handlers.
    Returns the configured logger instance.
    """
    global _logger

    if _logger is not None:
        return _logger

    _logger = logging.getLogger("llmXive")
    _logger.setLevel(level)
    _logger.handlers.clear()

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        _logger.addHandler(console_handler)

    if log_file:
        os.makedirs(os.path.dirname(log_file) or '.', exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(JSONFormatter())
        _logger.addHandler(file_handler)

    return _logger


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a message with additional context data attached as an attribute.
    """
    extra = {"context": context} if context else {}
    logger.log(level, message, extra=extra)


def get_global_error_tracker() -> ErrorTracker:
    """
    Returns the global error tracker instance, creating one if necessary.
    """
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = ErrorTracker()
    return _global_tracker
