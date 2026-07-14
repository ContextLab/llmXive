"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from config import get_paths


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
        self.output_path: str | None = None
        # Determine log file path from config
        try:
            paths = get_paths()
            log_dir = paths.get("logs")
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
                self.output_path = os.path.join(log_dir, "pipeline_run.json")
        except Exception:
            # Fallback if config not loaded yet
            self.output_path = "data/logs/pipeline_run.json"

    def _flush_to_disk(self, entry: LogEntry) -> None:
        """Append a log entry to the JSONL log file."""
        if not self.output_path:
            return
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        self._flush_to_disk(entry)
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


def log_stage_start(stage_name: str, *args: Any, **kwargs: Any) -> LogEntry:
    """Log the start of a pipeline stage.

    Accepts flexible signatures:
      - log_stage_start("name")
      - log_stage_start("name", detail_dict)
      - log_stage_start(logger, "name")
      - log_stage_start(logger, "name", detail_dict)
    """
    logger = None
    name = stage_name
    detail = {}

    # Handle flexible argument shapes
    if args and not isinstance(args[0], str):
        logger = args[0]
        args = args[1:]

    if args:
        name = args[0]
        if len(args) > 1 and isinstance(args[1], dict):
            detail = args[1]

    # Merge kwargs into detail
    detail.update(kwargs)

    entry = get_logger().log(
        f"Start {name}",
        stage=name,
        **detail
    )
    return entry


def log_stage_complete(stage_name: str, *args: Any, **kwargs: Any) -> LogEntry:
    """Log the completion of a pipeline stage."""
    logger = None
    name = stage_name
    detail = {}

    if args and not isinstance(args[0], str):
        logger = args[0]
        args = args[1:]

    if args:
        name = args[0]
        if len(args) > 1 and isinstance(args[1], dict):
            detail = args[1]

    detail.update(kwargs)

    entry = get_logger().log(
        f"Complete {name}",
        stage=name,
        **detail
    )
    return entry


def log_stage_error(stage_name: str, error_msg: str, *args: Any, **kwargs: Any) -> LogEntry:
    """Log an error during a pipeline stage."""
    logger = None
    name = stage_name
    detail = {"error": error_msg}

    if args and not isinstance(args[0], str):
        logger = args[0]
        args = args[1:]

    if args:
        name = args[0]
        if len(args) > 1 and isinstance(args[1], dict):
            detail.update(args[1])

    detail.update(kwargs)

    entry = get_logger().log(
        f"Error {name}",
        stage=name,
        **detail
    )
    return entry


def setup_logging(log_file: str | None = None) -> None:
    """Initialize the global logger with an optional specific output path."""
    global _GLOBAL_LOGGER
    if log_file:
        _GLOBAL_LOGGER = ReproducibilityLogger()
        _GLOBAL_LOGGER.output_path = log_file
    else:
        _GLOBAL_LOGGER = ReproducibilityLogger()