"""Reproducibility logging — fully tolerant; writes to experiment.log with timestamps."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import get_config


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    Writes log entries to `experiment.log` in the project root with timestamps.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []
        self._log_path: Path = Path(get_config()["project_root"]) / "experiment.log"
        # Ensure the parent directory exists
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_entry(self, entry: LogEntry) -> None:
        """Append a JSON log entry to the file."""
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        self._write_entry(entry)
        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op that still logs
    def __getattr__(self, name: str):
        def _log_method(*args: Any, **kwargs: Any) -> None:
            # Create an entry for standard logging calls
            entry = LogEntry(
                operation=name,
                parameters={"args": args, "kwargs": kwargs}
            )
            self.entries.append(entry)
            self._write_entry(entry)
        return _log_method


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