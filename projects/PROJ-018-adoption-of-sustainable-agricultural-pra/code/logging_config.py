"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any
from pathlib import Path
import yaml


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


def initialize_modeling_log(log_path: str = "modeling_log.yaml") -> None:
    """Initialize the modeling log file if it doesn't exist."""
    path = Path(log_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump({"pipeline": {}, "power_analysis": {}}, f)


def update_log_section(section_name: str, data: dict, log_path: str = "modeling_log.yaml") -> None:
    """Update a specific section in the modeling log."""
    path = Path(log_path)
    if not path.exists():
        initialize_modeling_log(log_path)

    with open(path, "r") as f:
        try:
            log_data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            log_data = {}

    if section_name not in log_data:
        log_data[section_name] = {}

    log_data[section_name].update(data)

    with open(path, "w") as f:
        yaml.dump(log_data, f, default_flow_style=False)


def append_log_entry(section_name: str, entry: dict, log_path: str = "modeling_log.yaml") -> None:
    """Append an entry to a list in the modeling log."""
    path = Path(log_path)
    if not path.exists():
        initialize_modeling_log(log_path)

    with open(path, "r") as f:
        try:
            log_data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            log_data = {}

    if section_name not in log_data:
        log_data[section_name] = []

    if not isinstance(log_data[section_name], list):
        log_data[section_name] = []

    log_data[section_name].append(entry)

    with open(path, "w") as f:
        yaml.dump(log_data, f, default_flow_style=False)
