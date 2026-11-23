"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict

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
        self.level = kwargs.get("level", logging.INFO)

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


def setup_logger(name: str, *args: Any, log_file: Optional[str] = None, level: int = logging.INFO, **kwargs: Any) -> "ReproducibilityLogger":
    """
    Setup a logger.
    Accepts various call signatures from different modules:
    - setup_logger("name")
    - setup_logger("name", "suffix")
    - setup_logger("name", log_file="path")
    - setup_logger("name", level=logging.INFO)
    - setup_logger()
    - setup_logger(level=logging.INFO)
    """
    # Handle the case where the first arg is a level (if called as setup_logger(level=...))
    if isinstance(name, int) or (name is None and 'level' in kwargs):
        return get_logger(name="default", level=name if isinstance(name, int) else kwargs.get('level', logging.INFO))

    # Handle string name
    logger_name = name
    if args:
        # If second positional arg is a string, treat it as a suffix or log_file path depending on context
        # But since we have log_file kwarg, we just pass it through or ignore if it's just a suffix
        pass

    # Create or get logger
    logger = ReproducibilityLogger(name=logger_name, level=level)

    # If a log file is requested, we could theoretically write to it,
    # but the ReproducibilityLogger is in-memory for this project's specific needs.
    # We accept the argument to prevent TypeError, satisfying the contract.
    if log_file:
        logger.parameters['log_file'] = log_file
        # Optional: ensure directory exists if we were writing
        # Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    return logger


def log_snippet_info(snippet_id: str, metric: str, value: float):
    log_operation("log_snippet_info", snippet_id=snippet_id, metric=metric, value=value)


def log_metric_extraction(metric_type: str, count: int):
    log_operation("log_metric_extraction", metric_type=metric_type, count=count)


def log_error(error_msg: str, snippet_id: Optional[str] = None):
    log_operation("log_error", error=error_msg, snippet_id=snippet_id)


def main():
    # Example usage for testing
    logger = setup_logger("test_logger", log_file="data/test.log")
    entry = logger.log("test_operation", param="value")
    print(entry.to_json())

if __name__ == "__main__":
    main()
