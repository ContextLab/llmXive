"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import time
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar("T", bound=Callable[..., Any])


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
        self.entries: List[LogEntry] = []
        self._warning_log: List[str] = []

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

    def capture_warning(self, msg: str) -> None:
        self._warning_log.append(msg)

    def get_captured_warnings(self) -> List[str]:
        return self._warning_log.copy()

    def clear_warnings(self) -> None:
        self._warning_log.clear()


_GLOBAL_LOGGER: Optional["ReproducibilityLogger"] = None


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


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    delay_seconds: Optional[float] = None,
    logger: Optional[ReproducibilityLogger] = None,
) -> Callable[[T], T]:
    """Decorator to retry a function on failure.

    Accepts both 'delay' and 'delay_seconds' for compatibility with various callers.
    If delay_seconds is provided, it takes precedence.
    """
    actual_delay = delay_seconds if delay_seconds is not None else delay

    def decorator(func: T) -> T:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        if logger:
                            logger.log(
                                "retry_attempt",
                                function=func.__name__,
                                attempt=attempt + 1,
                                max_attempts=max_attempts,
                                error=str(e),
                            )
                        time.sleep(actual_delay)
            if last_exception:
                raise last_exception
        return wrapper  # type: ignore
    return decorator


def capture_warning(msg: str) -> None:
    get_logger().capture_warning(msg)


def get_captured_warnings() -> List[str]:
    return get_logger().get_captured_warnings()


def clear_warnings() -> None:
    get_logger().clear_warnings()


def export_warning_log(path: str) -> None:
    import json
    warnings = get_captured_warnings()
    with open(path, "w") as f:
        json.dump(warnings, f, indent=2)


def log_retry_attempts(
    func_name: str,
    attempt: int,
    error: str,
    logger: Optional[ReproducibilityLogger] = None,
) -> None:
    target = logger or get_logger()
    target.log(
        "retry_attempt",
        function=func_name,
        attempt=attempt,
        error=error,
    )


def setup_logging(level: int = 20) -> None:
    """Setup logging (no-op for reproducibility logger, but kept for API compat)."""
    pass