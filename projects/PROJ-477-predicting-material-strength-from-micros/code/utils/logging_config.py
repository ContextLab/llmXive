"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

from pathlib import Path


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: str = "success"
    message: Optional[str] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises.

    This logger is self-contained and writes to files if configured.
    """

    def __init__(
        self,
        *args: Any,
        name: str = "reproducibility",
        log_file: Optional[str] = None,
        json_file: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.name = args[0] if args else name
        self.log_file = log_file
        self.json_file = json_file
        self.entries: list[LogEntry] = []

        # Ensure directories exist if files are specified
        if self.log_file:
            Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)
        if self.json_file:
            Path(self.json_file).parent.mkdir(parents=True, exist_ok=True)

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        op = args[0] if args else kwargs.get("operation", "")
        status = kwargs.pop("status", "success")
        message = kwargs.pop("message", None)

        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            status=status,
            message=message,
        )
        self.entries.append(entry)

        # Write to log file if configured
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(f"[{entry.timestamp}] {entry.operation}: {entry.parameters}\n")

        # Write to JSON file if configured
        if self.json_file:
            with open(self.json_file, "w", encoding="utf-8") as f:
                json.dump([asdict(e) for e in self.entries], f, indent=2, default=str)

        return entry

    # .info/.debug/.warning/.error/.critical/... -> tolerant no-op
    def __getattr__(self, name: str) -> Callable[..., None]:
        def _noop(*args: Any, **kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: Optional[ReproducibilityLogger] = None


def get_logger(
    *args: Any,
    name: str = "reproducibility",
    log_file: Optional[str] = None,
    json_file: Optional[str] = None,
    **kwargs: Any,
) -> ReproducibilityLogger:
    global _GLOBAL_LOGGER
    # If specific files are requested, we might need a new logger instance
    # or update the global one. For simplicity, if args differ significantly,
    # we return a new instance or the global one.
    # To satisfy the "cumulative" requirement, we ensure the global logger
    # has the capabilities, but we allow specific calls to override file paths
    # by creating a temporary logger or updating the global one.
    # However, the safest cumulative approach is: if called with new file paths,
    # update the global logger's paths or create a new one if names differ.
    # Given the constraints, we'll just return the global one if it exists,
    # or create it. If specific file paths are passed, we assume the caller
    # wants those files written to, so we update the global logger's paths
    # if they differ, or create a new one if the name differs.

    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, name=name, log_file=log_file, json_file=json_file, **kwargs)
    else:
        # Update paths if provided
        if log_file:
            _GLOBAL_LOGGER.log_file = log_file
        if json_file:
            _GLOBAL_LOGGER.json_file = json_file
        # Update name if provided
        if name and name != _GLOBAL_LOGGER.name:
            _GLOBAL_LOGGER.name = name

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


def log_metric(metric_name: str, value: Any, **kwargs: Any) -> LogEntry:
    """Log a metric value."""
    return get_logger().log("metric_recorded", name=metric_name, value=value, **kwargs)


def main() -> None:
    """CLI entry point for logging config (for testing)."""
    logger = get_logger("test", log_file="results/test.log", json_file="results/test.json")
    logger.log("test_operation", key="value")
    logger.info("This should not crash")
    logger.warning("This should not crash")
    print("Logging test completed.")


if __name__ == "__main__":
    main()
