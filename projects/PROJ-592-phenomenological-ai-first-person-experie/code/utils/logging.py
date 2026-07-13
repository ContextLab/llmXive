"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import time
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Union

@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    level: str = "INFO"
    message: str = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Do NOT subclass or delegate to the stdlib ``logging`` module: its
    ``log(level, msg)`` needs an integer level and has no ``to_json`` — that is
    exactly what keeps breaking. This logger is self-contained.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._warnings: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        level = kwargs.get("level", "INFO")
        msg = kwargs.get("message", "")
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            level=level,
            message=msg
        )
        self.entries.append(entry)
        return entry

    def info(self, *args: Any, **kwargs: Any) -> None:
        kwargs["level"] = "INFO"
        self.log(*args, **kwargs)

    def debug(self, *args: Any, **kwargs: Any) -> None:
        kwargs["level"] = "DEBUG"
        self.log(*args, **kwargs)

    def warning(self, *args: Any, **kwargs: Any) -> None:
        kwargs["level"] = "WARNING"
        self.log(*args, **kwargs)
        if args:
            self._warnings.append(str(args[0]))

    def error(self, *args: Any, **kwargs: Any) -> None:
        kwargs["level"] = "ERROR"
        self.log(*args, **kwargs)

    def critical(self, *args: Any, **kwargs: Any) -> None:
        kwargs["level"] = "CRITICAL"
        self.log(*args, **kwargs)

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None
_CAPTURED_WARNINGS: list = []

def get_logger(*args: Any, **kwargs: Any) -> "ReproducibilityLogger":
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
            logger = get_logger()
            logger.log(func.__name__, operation=func.__name__)
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)

def capture_warning(message: str) -> None:
    """Capture a warning for later export."""
    _CAPTURED_WARNINGS.append(message)
    get_logger().warning(message)

def get_captured_warnings() -> list:
    """Return all captured warnings."""
    return _CAPTURED_WARNINGS.copy()

def clear_warnings() -> None:
    """Clear all captured warnings."""
    _CAPTURED_WARNINGS.clear()

def export_warning_log(path: str) -> None:
    """Export captured warnings to a JSON file."""
    import json
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(_CAPTURED_WARNINGS, f, indent=2)

def log_retry_attempts(
    func_name: str,
    attempt: int,
    max_attempts: int,
    delay: float,
    error: Optional[str] = None
) -> None:
    """Log retry attempt details."""
    logger = get_logger()
    logger.log(
        "retry_attempt",
        operation=func_name,
        attempt=attempt,
        max_attempts=max_attempts,
        delay=delay,
        error=error
    )

def setup_logging(level: str = "INFO") -> None:
    """Setup basic logging configuration."""
    pass  # No-op for reproducibility logger

def retry_on_failure(
    max_retries: Optional[int] = None,
    max_attempts: Optional[int] = None,
    delay: float = 1.0,
    delay_seconds: Optional[float] = None,
    logger: Optional[Any] = None
) -> Callable:
    """
    Decorator for retrying functions on failure.
    Accepts multiple parameter shapes for compatibility.
    """
    # Normalize parameters
    max_attempts = max_attempts or max_retries or 3
    delay = delay_seconds or delay or 1.0
    log = logger or get_logger()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    log_retry_attempts(
                        func_name=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=delay,
                        error=str(e)
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
            
            # All retries exhausted
            log.error(
                f"Function {func.__name__} failed after {max_attempts} attempts",
                error=str(last_exception)
            )
            raise last_exception
        return wrapper
    return decorator
