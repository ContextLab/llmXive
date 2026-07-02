"""Reproducibility logging — fully tolerant; raises on nothing.

This module provides a lightweight logger that records log entries in memory,
attaches UTC timestamps, and writes any error‑level messages to a persistent
``experiment.log`` file. It is deliberately independent of the standard library
``logging`` module to avoid incompatibilities with the project's custom logging
contracts.
"""

from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class LogEntry:
    """A single log record."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialize the entry to a JSON line."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A tolerant logger that never raises and writes error logs to a file.

    - All calls are accepted; unknown methods become no‑ops.
    - ``log`` stores the entry in memory and returns a :class:`LogEntry`.
    - ``error`` (and any call to ``log`` with operation ``'error'``) is also
      persisted to ``experiment.log`` on disk, one JSON line per entry.
    """

    _DEFAULT_LOG_FILE = Path("experiment.log")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # ``name`` is kept for API compatibility; it is not used internally.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []
        # Resolve log‑file path – allow callers to override via ``log_file`` kwarg.
        self.log_file: Path = Path(kwargs.get("log_file", self._DEFAULT_LOG_FILE))
        # Ensure the parent directory exists (log file may be in a sub‑dir).
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core logging API
    # ------------------------------------------------------------------
    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Record a generic log entry.

        The first positional argument (if any) is interpreted as the operation
        name; otherwise ``operation`` must be supplied via a keyword argument.
        All remaining positional/keyword arguments are stored in ``parameters``.

        If the operation is ``'error'`` (case‑insensitive) the entry is also
        appended to ``experiment.log`` on disk.
        """
        op = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)

        # Persist error‑level entries.
        if str(op).lower() == "error":
            self._write_to_file(entry)
        return entry

    # ------------------------------------------------------------------
    # Convenience level methods (info/debug/warning/error/critical)
    # ------------------------------------------------------------------
    def info(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log an informational message."""
        return self.log("info", *args, **kwargs)

    def debug(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log a debug message."""
        return self.log("debug", *args, **kwargs)

    def warning(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log a warning message."""
        return self.log("warning", *args, **kwargs)

    def error(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log an error message and write it to ``experiment.log``."""
        return self.log("error", *args, **kwargs)

    def critical(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Log a critical error (treated the same as ``error`` for persistence)."""
        return self.log("critical", *args, **kwargs)

    # ------------------------------------------------------------------
    # Fallback for any other attribute – tolerant no‑op
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        """Return a no‑op callable for any undefined attribute."""

        def _noop(*args: Any, **kwargs: Any) -> None:
            return None

        return _noop

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _write_to_file(self, entry: LogEntry) -> None:
        """Append a JSON representation of *entry* to the log file."""
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(entry.to_json() + "\n")
        except Exception:
            # Logging must never raise; failures are silently ignored.
            pass


# ----------------------------------------------------------------------
# Global singleton accessor
# ----------------------------------------------------------------------
_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a process‑wide singleton logger.

    The first call can optionally pass ``name`` or ``log_file``; subsequent
    calls ignore those arguments and return the same instance.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose helper: can be used as a decorator or a direct logging call.

    - As a decorator: ``@log_operation`` wraps a function without altering its
      signature.
    - As a function call: ``log_operation('my_op', key=value)`` records a log
      entry and returns the resulting :class:`LogEntry`.
    """
    # Decorator usage.
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Direct‑call usage.
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)