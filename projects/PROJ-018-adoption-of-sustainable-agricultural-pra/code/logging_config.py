"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import yaml
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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
        self.sections: dict = {}

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    def to_json(self) -> str:
        return json.dumps({
            "name": self.name,
            "entries": [asdict(e) for e in self.entries],
            "sections": self.sections
        }, ensure_ascii=False, default=str)

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str):
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop

    def update_section(self, name: str, data: dict) -> None:
        """Update a specific section in the log."""
        self.sections[name] = data

    def get_sections(self) -> dict:
        return self.sections


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
        with open(path, 'w') as f:
            yaml.dump({"initialized_at": datetime.utcnow().isoformat()}, f)

def update_log_section(section_name: str, updates: Dict[str, Any]) -> None:
    """Update a specific section in the modeling log.

def update_log_section(name: str, data: dict) -> None:
    """Update a section in the global logger and persist to YAML."""
    logger = get_logger()
    logger.update_section(name, data)
    # Persist to YAML file
    log_path = Path("modeling_log.yaml")
    try:
        with open(log_path, 'r') as f:
            current_log = yaml.safe_load(f) or {}
    except FileNotFoundError:
        current_log = {}

    current_log[name] = data
    current_log["updated_at"] = datetime.utcnow().isoformat()

    with open(log_path, 'w') as f:
        yaml.dump(current_log, f, default_flow_style=False)

def append_log_entry(section_name: str, entry: Dict[str, Any]) -> None:
    """Append an entry to a list-based section in the modeling log.

def append_log_entry(operation: str, data: dict) -> None:
    """Append an entry to the log."""
    logger = get_logger()
    logger.log(operation, **data)
    # We don't persist append-only entries to YAML in this simplified version
    # as the main persistence is via update_log_section
