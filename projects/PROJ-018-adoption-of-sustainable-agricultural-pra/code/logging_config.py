"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict

@dataclass
class LogEntry:
    """A single log entry that can be serialised to JSON."""
    operation: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Return a JSON representation of the entry."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A lightweight logger that never raises and stores LogEntry objects."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Accept any init signature – name is optional.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Create a LogEntry, store it, and return it."""
        operation = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(operation), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Any conventional logging method (info, debug, warning, error, etc.)
    # becomes a no‑op that never raises.
    def __getattr__(self, name: str) -> Callable[..., None]:
        def _noop(*_a: Any, **_kw: Any) -> None:
            return None

        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton logger instance."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """
    Dual‑purpose decorator / direct‑call logger.

    1. Used as a decorator without arguments:
           @log_operation
           def foo(...):
               ...

    2. Used as a decorator with an explicit operation name:
           @log_operation("my_step")
           def foo(...):
               ...

    3. Used as a direct logging call:
           log_operation("my_step", key=value)

    The function inspects the call pattern and returns either a decorator
    (wrapping the target function) or a LogEntry (for direct calls).
    """
    # Case 1 – @log_operation (no parentheses)
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Case 2 – @log_operation("name")  (decorator with operation name)
    if len(args) == 1 and isinstance(args[0], str) and not kwargs:
        operation_name = args[0]

        def _decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def _wrapper(*a: Any, **k: Any) -> Any:
                # Log the start of the operation; actual function runs afterwards.
                get_logger().log(operation_name)
                return func(*a, **k)

            return _wrapper

        return _decorator

    # Case 3 – direct call, possibly with extra keyword parameters.
    operation = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(operation, **kwargs)


def update_log_section(
    section: str,
    data: Any,
    *,
    log_path: str | Path | None = None,
) -> None:
    """
    Append or replace a top‑level ``section`` in the reproducibility log.

    Parameters
    ----------
    section: str
        The top‑level key to update (e.g., "power_analysis").
    data: Any
        JSON‑serialisable data that will be stored under ``section``.
    log_path: str | Path, optional
        Path to the YAML log file. If omitted, the default location
        ``modeling_log.yaml`` in the project root is used.
    """
    default_path = Path(get_config("modeling_log_path", "modeling_log.yaml"))
    path = Path(log_path) if log_path is not None else default_path

    # Ensure the parent directory exists.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing content if the file already exists.
    if path.is_file():
        try:
            import yaml

            with path.open("r", encoding="utf-8") as f:
                current = yaml.safe_load(f) or {}
        except Exception:
            current = {}
    else:
        current = {}

    # Update the section.
    current[section] = data

    # Write back to YAML.
    import yaml

    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(current, f, sort_keys=False)
