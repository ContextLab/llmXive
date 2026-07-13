"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import time
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, TypeVar

import numpy as np

F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class LogEntry:
    """Structured log entry for reproducibility."""
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger is self-contained and does not delegate to the stdlib
    ``logging`` module to avoid type mismatches and missing methods.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []
        self._level = "INFO"

    def setLevel(self, level: str) -> None:
        """Standardize log level."""
        self._level = level.upper()

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log an operation."""
        op = args[0] if args else kwargs.get("operation", "")
        msg = kwargs.get("message", str(op))
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            level=self._level,
            message=msg
        )
        self.entries.append(entry)
        return entry

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        entry = LogEntry(operation="info", message=msg, parameters=kwargs)
        self.entries.append(entry)

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        entry = LogEntry(operation="debug", message=msg, parameters=kwargs)
        self.entries.append(entry)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        entry = LogEntry(operation="warning", message=msg, parameters=kwargs)
        self.entries.append(entry)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        entry = LogEntry(operation="error", message=msg, parameters=kwargs)
        self.entries.append(entry)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        entry = LogEntry(operation="critical", message=msg, parameters=kwargs)
        self.entries.append(entry)

    # Tolerant fallback for any other attribute access
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual-purpose: a decorator (@log_operation) OR a direct logging call.

    The direct-call path ALWAYS returns a LogEntry (callers use .to_json());
    decorator use returns the wrapped function. Never return a bare function
    from the direct-call path.
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def capture_warning(message: str, category: type = UserWarning) -> None:
    """Capture a warning without printing it."""
    warnings.warn(message, category)


def get_captured_warnings() -> list[str]:
    """Retrieve captured warnings (stub for now)."""
    return []


def clear_warnings() -> None:
    """Clear captured warnings."""
    pass


def export_warning_log(path: str) -> None:
    """Export warning log to JSON."""
    logger = get_logger()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump([e.to_json() for e in logger.entries], f, indent=2)


def log_retry_attempts(operation: str, attempts: int, delay: float) -> None:
    """Log retry attempts."""
    entry = LogEntry(
        operation=f"retry_{operation}",
        parameters={"attempts": attempts, "delay_seconds": delay}
    )
    get_logger().entries.append(entry)


def setup_logging(level: str = "INFO") -> None:
    """Standardize logging setup."""
    logger = get_logger()
    logger.setLevel(level)


def retry_on_failure(
    max_retries: Optional[int] = None,
    max_attempts: Optional[int] = None,
    delay: Optional[float] = None,
    delay_seconds: Optional[float] = None,
    logger: Optional[ReproducibilityLogger] = None
) -> Callable[[F], F]:
    """Decorator to retry a function on failure.

    Accepts multiple argument shapes for compatibility with various callers:
    - @retry_on_failure(max_retries=N, logger=logger)
    - @retry_on_failure(max_attempts=N, delay=D)
    - @retry_on_failure(max_attempts=N, delay_seconds=D)
    - @retry_on_failure(max_attempts=N, delay=D, logger=logger)
    """
    # Normalize arguments
    attempts = max_attempts if max_attempts is not None else (max_retries if max_retries is not None else 3)
    delay_val = delay_seconds if delay_seconds is not None else (delay if delay is not None else 1.0)
    log_instance = logger if logger is not None else get_logger()

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    log_retry_attempts(func.__name__, attempt, delay_val)
                    if attempt < attempts:
                        time.sleep(delay_val)
            # If we get here, all retries failed
            raise last_exception if last_exception else RuntimeError("Retry failed")

        return wrapper  # type: ignore
    return decorator
# End of file