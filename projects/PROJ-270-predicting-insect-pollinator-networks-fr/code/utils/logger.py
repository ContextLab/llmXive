"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging as stdlib_logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
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
        # Optional: attach a stdlib logger if configured
        self._stdlib_logger = None
        if "std_logger" in kwargs:
            self._stdlib_logger = kwargs["std_logger"]
        elif "log_file" in kwargs or "log_level" in kwargs:
            # Configure a stdlib logger for file output if requested
            self._stdlib_logger = stdlib_logging.getLogger(f"file_{self.name}")
            self._stdlib_logger.setLevel(stdlib_logging.INFO)
            if not self._stdlib_logger.handlers:
                handler = stdlib_logging.FileHandler(kwargs.get("log_file", "reproducibility.log"))
                formatter = stdlib_logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self._stdlib_logger.addHandler(handler)
                if "log_level" in kwargs:
                    lvl = kwargs["log_level"]
                    if isinstance(lvl, str):
                        lvl = getattr(stdlib_logging, lvl.upper(), stdlib_logging.INFO)
                    elif isinstance(lvl, int):
                        pass # Already an int
                    self._stdlib_logger.setLevel(lvl)

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)

        # Write to stdlib logger if available
        if self._stdlib_logger:
            msg = entry.to_json()
            self._stdlib_logger.info(msg)

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


def setup_logging(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """
    Setup the global logging infrastructure.
    Tolerant of different call signatures:
      1. setup_logging() -> basic init
      2. setup_logging(log_level=logging.INFO, log_file=Path(...)) -> configure file/std logger
    """
    global _GLOBAL_LOGGER
    # Extract specific kwargs for configuration
    log_file = kwargs.pop("log_file", None)
    log_level = kwargs.pop("log_level", None)

    # If we already have a logger and no new config requested, return it
    if _GLOBAL_LOGGER is not None and not log_file and not log_level:
        return _GLOBAL_LOGGER

    # Prepare kwargs for the ReproducibilityLogger
    logger_kwargs = {}
    if log_file:
        logger_kwargs["log_file"] = log_file
    if log_level:
        logger_kwargs["log_level"] = log_level

    _GLOBAL_LOGGER = ReproducibilityLogger(*args, **logger_kwargs)
    return _GLOBAL_LOGGER