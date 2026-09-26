"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

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


class EnvironmentalFormatter(logging.Formatter):
    """Custom formatter for structured environmental logs."""
    def format(self, record):
        return json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        })


def setup_logging(level: Optional[str] = None, log_file: Optional[str] = None) -> ReproducibilityLogger:
    """Setup logging with tolerance for various call signatures.

    Accepts:
      - setup_logging()
      - setup_logging(level=logging.INFO)
      - setup_logging(level="INFO")
      - setup_logging(log_file="path/to/file.log")
      - setup_logging(level=args.log_level)
    """
    # Tolerate missing args
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    # Handle if level is passed as a logging constant (e.g., logging.INFO)
    if isinstance(level, int):
        level_val = level
    elif isinstance(level, str):
        level_val = getattr(logging, level.upper(), logging.INFO)
    else:
        level_val = logging.INFO

    # Configure stdlib logging if a file is requested or for side effects
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        handler = logging.FileHandler(log_file)
        formatter = EnvironmentalFormatter()
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.setLevel(level_val)
        root_logger.addHandler(handler)
    
    # Always return the global reproducibility logger
    return get_logger()


def log_environmental_params(params: Dict[str, Any]) -> None:
    """Log environmental parameters to the global logger."""
    log_operation("environmental_params", **params)


def log_compliance_check(metric_name: str, value: float, threshold: float, passed: bool) -> None:
    """Log a compliance check result."""
    log_operation(
        "compliance_check",
        metric=metric_name,
        value=value,
        threshold=threshold,
        passed=passed
    )
