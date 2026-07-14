"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

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
    if not os.path.exists(log_path):
        with open(log_path, 'w') as f:
            yaml.dump({"_metadata": {"created_at": datetime.utcnow().isoformat()}}, f)

def update_log_section(section_name: str, updates: Dict[str, Any]) -> None:
    """Update a specific section in the modeling log.

    Args:
        section_name: The top-level key to update/create
        updates: Dictionary of key-value pairs to update in that section
    """
    log_path = "modeling_log.yaml"
    initialize_modeling_log(log_path)

    try:
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    except Exception:
        log_data = {}

    if section_name not in log_data:
        log_data[section_name] = {}

    log_data[section_name].update(updates)
    log_data[section_name]["updated_at"] = datetime.utcnow().isoformat()

    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)

def append_log_entry(section_name: str, entry: Dict[str, Any]) -> None:
    """Append an entry to a list-based section in the modeling log.

    Args:
        section_name: The top-level key containing a list
        entry: Dictionary to append to the list
    """
    log_path = "modeling_log.yaml"
    initialize_modeling_log(log_path)

    try:
        with open(log_path, 'r') as f:
            log_data = yaml.safe_load(f) or {}
    except Exception:
        log_data = {}

    if section_name not in log_data:
        log_data[section_name] = []

    if not isinstance(log_data[section_name], list):
        log_data[section_name] = []

    entry["timestamp"] = datetime.utcnow().isoformat()
    log_data[section_name].append(entry)

    with open(log_path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)
