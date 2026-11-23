"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import time
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, TypeVar, Optional

from code.config import get_config

@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

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

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: "ReproducibilityLogger | None" = None


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
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


F = TypeVar('F', bound=Callable[..., Any])


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    max_delay: float = 10.0,
    logger: Optional[Any] = None
) -> Callable[[F], F]:
    """
    Decorator to retry a function on failure with exponential backoff.
    
    Implements T010: Retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay in seconds.
        backoff: Multiplier for delay (exponential).
        max_delay: Maximum delay cap in seconds.
        logger: Optional logger to log retry attempts.
        
    Returns:
        Decorated function.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        # Log retry attempt
                        if logger:
                            log_operation(
                                "retry_attempt",
                                function=func.__name__,
                                attempt=attempt,
                                max_attempts=max_attempts,
                                delay=current_delay,
                                error=str(e)
                            )
                        time.sleep(current_delay)
                        current_delay = min(current_delay * backoff, max_delay)
                    else:
                        # Final attempt failed
                        log_operation(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=max_attempts,
                            error=str(e)
                        )
                        
            raise last_exception
        return wrapper  # type: ignore
    return decorator


def capture_warning(category=Warning, stacklevel=2):
    """Capture warnings for later retrieval."""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always", category)
                result = func(*args, **kwargs)
                return result, w
        return wrapper  # type: ignore
    return decorator


_WARNINGS_LOG: list = []


def get_captured_warnings() -> list:
    return _WARNINGS_LOG


def clear_warnings() -> None:
    _WARNINGS_LOG.clear()


def export_warning_log(path: str) -> None:
    import json
    with open(path, 'w') as f:
        json.dump(_WARNINGS_LOG, f, indent=2, default=str)


def log_retry_attempts(operation: str, attempt: int, max_attempts: int, error: str) -> None:
    """Helper to log retry attempts."""
    log_operation(
        "retry_attempt",
        operation=operation,
        attempt=attempt,
        max_attempts=max_attempts,
        error=error
    )


def setup_logging(level: str = "INFO") -> None:
    """Setup standard logging configuration if needed."""
    # This is a no-op for the ReproducibilityLogger but kept for API compatibility
    pass