"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging as stdlib_logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

# Standard library logger for actual output
_STD_LOGGER = stdlib_logging.getLogger("llmXive")
_STD_LOGGER.setLevel(stdlib_logging.INFO)
if not _STD_LOGGER.handlers:
    handler = stdlib_logging.StreamHandler()
    formatter = stdlib_logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    _STD_LOGGER.addHandler(handler)


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
        # Also log to stdlib logger for visibility
        _STD_LOGGER.info(f"[{self.name}] {op}: {kwargs}")
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op or delegation
    def __getattr__(self, name: str):
        def _handler(*args: Any, **kwargs: Any) -> Any:
            # Defer to stdlib logger for actual output
            if hasattr(_STD_LOGGER, name):
                getattr(_STD_LOGGER, name)(*args, **kwargs)
            return None
        return _handler


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


# Backward compatibility wrappers for the specific signatures used in the codebase
def log_info(*args: Any, **kwargs: Any) -> None:
    """
    Tolerant log_info that accepts:
    1. log_info(logger, message) -> uses logger.info
    2. log_info(message) -> uses global logger
    3. log_info(operation, **params) -> uses log_operation
    """
    if len(args) == 0:
        return

    # Case 1: log_info(logger, message)
    if len(args) >= 2 and hasattr(args[0], 'info'):
        logger = args[0]
        message = args[1]
        logger.info(message)
        return

    # Case 2: log_info(message)
    if len(args) == 1 and isinstance(args[0], str):
        _STD_LOGGER.info(args[0])
        return

    # Case 3: log_info(operation, **params)
    if len(args) >= 1:
        op = args[0]
        log_operation(op, **kwargs)
        return

    # Fallback
    _STD_LOGGER.info(str(args) if args else str(kwargs))


def log_warning(*args: Any, **kwargs: Any) -> None:
    """Tolerant log_warning."""
    if len(args) >= 2 and hasattr(args[0], 'warning'):
        args[0].warning(args[1])
    elif len(args) == 1 and isinstance(args[0], str):
        _STD_LOGGER.warning(args[0])
    else:
        _STD_LOGGER.warning(str(args) if args else str(kwargs))


def log_error(*args: Any, **kwargs: Any) -> None:
    """Tolerant log_error."""
    if len(args) >= 2 and hasattr(args[0], 'error'):
        args[0].error(args[1])
    elif len(args) == 1 and isinstance(args[0], str):
        _STD_LOGGER.error(args[0])
    else:
        _STD_LOGGER.error(str(args) if args else str(kwargs))


def log_debug(*args: Any, **kwargs: Any) -> None:
    """Tolerant log_debug."""
    if len(args) >= 2 and hasattr(args[0], 'debug'):
        args[0].debug(args[1])
    elif len(args) == 1 and isinstance(args[0], str):
        _STD_LOGGER.debug(args[0])
    else:
        _STD_LOGGER.debug(str(args) if args else str(kwargs))
