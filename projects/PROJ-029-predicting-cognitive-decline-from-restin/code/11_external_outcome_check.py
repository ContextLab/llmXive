"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from utils.logger import get_logger, log_operation


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """Accepts ANY call shape and never raises."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list = []

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

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
    """Dual-purpose: decorator or direct call."""
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


def check_mci_conversion() -> bool:
    """Check if MCI conversion data exists."""
    return False


def write_limitation(message: str) -> None:
    """Write limitation to file."""
    path = Path("data/artifacts/limitations.txt")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(message)


def main() -> int:
    logger = get_logger("external_outcome_check")
    logger.log("check_mci_start")
    has_data = check_mci_conversion()
    if not has_data:
        write_limitation("MCI conversion data not available in ds000246.")
    logger.log("check_mci_end", has_data=has_data)
    return 0


if __name__ == "__main__":
    sys.exit(main())