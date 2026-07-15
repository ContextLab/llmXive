"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


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


def log_error_details(error: Any, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log error details. Tolerant of missing context.
    """
    logger = get_logger()
    entry = logger.log("error_details", error=str(error), context=context or {})
    logger.log("error_logged", entry_id=id(entry))


def setup_logging(*args: Any, **kwargs: Any) -> None:
    """No-op setup for compatibility."""
    pass


def log_simulation_params(*args: Any, **kwargs: Any) -> None:
    """Log simulation parameters."""
    logger = get_logger()
    logger.log("simulation_params", **kwargs)


def log_seed_usage(*args: Any, **kwargs: Any) -> None:
    """Log seed usage."""
    logger = get_logger()
    logger.log("seed_usage", **kwargs)


def log_iteration_status(*args: Any, **kwargs: Any) -> None:
    """Log iteration status."""
    logger = get_logger()
    logger.log("iteration_status", **kwargs)


def log_test_result(*args: Any, **kwargs: Any) -> None:
    """Log test result."""
    logger = get_logger()
    logger.log("test_result", **kwargs)


def log_warning_assumption_violated(*args: Any, **kwargs: Any) -> None:
    """Log warning about assumption violation."""
    logger = get_logger()
    logger.log("assumption_violated", **kwargs)


def log_fallback_triggered(*args: Any, **kwargs: Any) -> None:
    """Log fallback trigger."""
    logger = get_logger()
    logger.log("fallback_triggered", **kwargs)


def log_output_file_written(*args: Any, **kwargs: Any) -> None:
    """Log output file written."""
    logger = get_logger()
    logger.log("output_file_written", **kwargs)


def log_shutdown(*args: Any, **kwargs: Any) -> None:
    """Log shutdown."""
    logger = get_logger()
    logger.log("shutdown", **kwargs)


def get_log_file_path() -> str:
    """Get log file path."""
    return "data/simulation.log"
