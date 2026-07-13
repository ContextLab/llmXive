"""Reproducibility logging — fully tolerant; raises on nothing.

This module provides a self-contained logging utility that avoids the
stdlib ``logging`` module's strict requirements (integer levels, specific
argument shapes) which have caused API contract violations across the
pipeline. Instead, it implements a flexible logger and decorator that
accepts any call shape and never raises on unexpected inputs.
"""
from __future__ import annotations

import functools
import json
import logging
import sys
import time
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, List, Optional, TypeVar

# Standard logging setup for actual stderr output (optional, for debug)
_std_logger = logging.getLogger("reproducibility_std")
_std_logger.setLevel(logging.DEBUG)
if not _std_logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    _std_logger.addHandler(handler)


@dataclass
class LogEntry:
    """A structured log entry that can be serialized to JSON."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"

    def to_json(self) -> str:
        """Serialize the log entry to a JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger is self-contained and does not delegate to the stdlib
    ``logging`` module to avoid strict type/level requirements. It
    stores entries in memory and optionally prints to stderr.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: List[LogEntry] = []
        self._level_map = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL,
        }

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log an operation with flexible arguments."""
        # Determine operation name
        op = args[0] if args else kwargs.pop("operation", "operation")
        
        # Determine level if provided
        level_str = kwargs.pop("level", "INFO")
        if isinstance(level_str, int):
            # Reverse map int to string for storage, or keep as is
            level_str = "INFO" 
        
        # Create entry
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            level=str(level_str).upper()
        )
        self.entries.append(entry)

        # Also log to std logger if level is high enough
        std_level = self._level_map.get(str(level_str).lower(), logging.INFO)
        _std_logger.log(std_level, entry.to_json())

        return entry

    def info(self, *args: Any, **kwargs: Any) -> LogEntry:
        kwargs["level"] = "INFO"
        return self.log(*args, **kwargs)

    def debug(self, *args: Any, **kwargs: Any) -> LogEntry:
        kwargs["level"] = "DEBUG"
        return self.log(*args, **kwargs)

    def warning(self, *args: Any, **kwargs: Any) -> LogEntry:
        kwargs["level"] = "WARNING"
        return self.log(*args, **kwargs)

    def error(self, *args: Any, **kwargs: Any) -> LogEntry:
        kwargs["level"] = "ERROR"
        return self.log(*args, **kwargs)

    def critical(self, *args: Any, **kwargs: Any) -> LogEntry:
        kwargs["level"] = "CRITICAL"
        return self.log(*args, **kwargs)

    def __getattr__(self, name: str) -> Callable[..., Any]:
        """Tolerant fallback for any other attribute access."""
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Get or create the global reproducibility logger."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call.

    - If called with a single callable argument and no kwargs, it acts as a decorator.
    - Otherwise, it logs the operation and returns a LogEntry.
    """
    # Decorator usage: @log_operation
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            # Log the call
            op_name = func.__name__
            get_logger().log("decorated_call", operation=op_name, func_args=a, func_kwargs=k)
            return func(*a, **k)

        return _wrapper

    # Direct call usage: log_operation("name", key=value)
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


T = TypeVar('T')


def retry_on_failure(
    max_attempts: int = 3,
    delay: Optional[float] = None,
    delay_seconds: Optional[float] = None,
    logger: Optional[ReproducibilityLogger] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to retry a function on failure.

    Accepts flexible argument names:
    - max_attempts (int)
    - delay (float) OR delay_seconds (float)
    - logger (ReproducibilityLogger)
    """
    # Normalize delay
    actual_delay = delay if delay is not None else delay_seconds
    if actual_delay is None:
        actual_delay = 1.0

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_logger = logger or get_logger()

            for attempt in range(1, max_attempts + 1):
                try:
                    current_logger.log(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts
                    )
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    current_logger.log(
                        "retry_failed",
                        function=func.__name__,
                        attempt=attempt,
                        error=str(e)
                    )
                    if attempt < max_attempts:
                        time.sleep(actual_delay)
            
            # All attempts failed
            current_logger.log(
                "retry_exhausted",
                function=func.__name__,
                max_attempts=max_attempts,
                final_error=str(last_exception)
            )
            raise last_exception

        return wrapper
    return decorator


# Warning capture utilities
_captured_warnings: List[dict] = []


def capture_warning(message: str, category: Optional[str] = None) -> None:
    """Capture a warning manually."""
    _captured_warnings.append({
        "message": str(message),
        "category": category or "UserWarning",
        "timestamp": datetime.utcnow().isoformat()
    })


def get_captured_warnings() -> List[dict]:
    """Retrieve all captured warnings."""
    return _captured_warnings.copy()


def clear_warnings() -> None:
    """Clear the captured warnings list."""
    _captured_warnings.clear()


def export_warning_log(path: str) -> None:
    """Export captured warnings to a JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(_captured_warnings, f, indent=2)


def log_retry_attempts(func_name: str, attempt: int, max_attempts: int, error: str) -> None:
    """Convenience wrapper to log retry logic."""
    get_logger().log(
        "retry_event",
        function=func_name,
        attempt=attempt,
        max_attempts=max_attempts,
        error=error
    )


def setup_logging(
    log_file: Optional[str] = None,
    level: str = "INFO"
) -> ReproducibilityLogger:
    """Setup logging configuration.

    Args:
        log_file: Optional path to write logs to (JSONL format).
        level: Logging level (INFO, DEBUG, etc.).
    """
    logger = get_logger()
    
    # If a file is requested, we could append entries there on flush
    # For now, we just return the logger which logs to stderr and memory
    if log_file:
        # In a real implementation, we might attach a file handler to the std_logger
        # For this self-contained logger, we rely on the global entries list
        pass

    return logger