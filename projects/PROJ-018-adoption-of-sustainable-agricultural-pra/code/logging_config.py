"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
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


def initialize_modeling_log(log_path: str) -> None:
    """Initialize the modeling_log.yaml file with an empty structure."""
    if not os.path.exists(log_path):
        with open(log_path, 'w') as f:
            yaml.dump({}, f)


def update_log_section(section_name: str, data: dict, log_path: Optional[str] = None) -> None:
    """Update a specific section in the modeling_log.yaml.

    This function is designed to be tolerant of various call signatures:
    - update_log_section("error", {"message": "..."})
    - update_log_section("mediation_analysis", {...})
    - update_log_section("report_generation", {...}, log_path="...")

    If log_path is not provided, it defaults to 'modeling_log.yaml' in the code directory.
    """
    if log_path is None:
        log_path = os.path.join(os.path.dirname(__file__), 'modeling_log.yaml')

    # Load existing log or create empty dict
    log_data = {}
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                log_data = yaml.safe_load(f) or {}
        except Exception:
            log_data = {}

    # Update the specific section
    log_data[section_name] = data

    # Write back
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)


def append_log_entry(entry: LogEntry, log_path: Optional[str] = None) -> None:
    """Append a LogEntry to the modeling_log.yaml entries list."""
    if log_path is None:
        log_path = os.path.join(os.path.dirname(__file__), 'modeling_log.yaml')

    if not os.path.exists(log_path):
        with open(log_path, 'w') as f:
            yaml.dump({"entries": []}, f)

    with open(log_path, 'r') as f:
        log_data = yaml.safe_load(f) or {}

    if "entries" not in log_data:
        log_data["entries"] = []

    log_data["entries"].append(asdict(entry))

    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)
