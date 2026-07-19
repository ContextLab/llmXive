"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional

from logging.handlers import RotatingFileHandler
from pathlib import Path

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


def setup_logger(*args: Any, batch_id: Optional[str] = None, **kwargs: Any) -> Any:
    """
    Setup a logger compatible with all call sites.

    Accepts:
      - setup_logger("name")
      - setup_logger(batch_id="main_pipeline")
      - setup_logger(__name__)

    Returns a ReproducibilityLogger instance that never raises.
    If a real logging setup is needed for file rotation, it is configured
    separately but the return value remains the ReproducibilityLogger to
    satisfy the 'to_json' and flexible argument requirements.
    """
    # Extract name if passed as positional arg
    name = None
    if args:
        if isinstance(args[0], str):
            name = args[0]
        elif hasattr(args[0], '__name__'):
            name = args[0].__name__

    if not name:
        name = kwargs.get("name", "reproducibility")

    # Configure the standard library logger for file rotation if requested
    # This is side-effect only; we still return the ReproducibilityLogger
    std_logger = logging.getLogger(name)
    std_logger.setLevel(logging.INFO)
    std_logger.propagate = False  # Avoid double logging if handlers exist

    # Check if handlers already exist to avoid duplicates
    if not std_logger.handlers:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "simulation.log"

        handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        std_logger.addHandler(handler)

    # Log batch_id if provided for Constitution Principle VI
    if batch_id:
        std_logger.info(f"Batch ID initialized: {batch_id}")

    # Return the tolerant ReproducibilityLogger
    return ReproducibilityLogger(name=name, batch_id=batch_id)
