"""Reproducibility logging — fully tolerant; raises on nothing.

This module provides a tolerant logger used across the project and implements
the external outcome check required by task T025. The logger is deliberately
simple and avoids delegating to the stdlib ``logging`` module so that all
callers (which expect a ``log`` method returning a ``LogEntry`` and attribute
accessors like ``info``/``debug``) work without error.
"""

from __future__ import annotations

import functools
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class LogEntry:
    """A single log record."""

    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialise the entry to JSON."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """A very permissive logger that never raises.

    It stores ``LogEntry`` objects internally and provides no‑op methods for
    typical logging levels (``info``, ``debug`` …) so any call shape is accepted.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # ``name`` is optional – we keep it for possible downstream use.
        self.name = args[0] if args else kwargs.get("name", "reproducibility")
        self.entries: list[LogEntry] = []

    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """Create a ``LogEntry`` from the supplied arguments."""
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(operation=str(op), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Provide tolerant no‑op methods for standard logging levels.
    def __getattr__(self, name: str):
        def _noop(*_args: Any, **_kwargs: Any) -> None:
            return None
        return _noop


_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return a singleton ``ReproducibilityLogger`` instance.

    Accepts any positional or keyword arguments (e.g. a name) and creates the
    logger on first call. Subsequent calls return the same instance.
    """
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any) -> Any:
    """Dual‑purpose: a decorator or a direct logging call.

    * As a decorator without arguments::

          @log_operation
          def foo(...):
              ...

    * As a decorator with an explicit operation name::

          @log_operation("my_operation")
          def foo(...):
              ...

    * As a direct call::

          log_operation("my_operation", key=value)

    The decorator form returns the original function unchanged (the
    surrounding infrastructure handles the actual logging). The direct‑call
    form returns a ``LogEntry`` instance.
    """
    # Decorator usage without parameters: @log_operation
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any) -> Any:
            return func(*a, **k)

        return _wrapper

    # Decorator usage with a name: @log_operation("name")
    if len(args) == 1 and isinstance(args[0], str) and not kwargs:
        operation_name = args[0]

        def decorator(func):
            @functools.wraps(func)
            def _wrapper(*a: Any, **k: Any) -> Any:
                # Log the operation before calling the function.
                get_logger().log(operation_name, **k)
                return func(*a, **k)
            return _wrapper
        return decorator

    # Direct‑call usage.
    op = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(op, **kwargs)


# ----------------------------------------------------------------------
# External outcome check implementation (Task T025)
# ----------------------------------------------------------------------

@dataclass
class LimitationNote:
    """Simple container for the limitation note text."""

    text: str = (
        "Limitation: MCI conversion data not available in the OpenNeuro "
        "dataset ds000246. External outcome analysis cannot be performed."
    )

    def write(self, path: Path) -> None:
        """Write the limitation note to ``path``."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(self.text + "\n")


def _find_mci_column(df: pd.DataFrame) -> str | None:
    """Return the name of a column that appears to contain MCI conversion data.

    The heuristic looks for column names containing the substrings
    ``mci`` and ``convert`` (case‑insensitive). If multiple columns match,
    the first one is returned.
    """
    candidates = [
        col
        for col in df.columns
        if ("mci" in col.lower()) and ("convert" in col.lower())
    ]
    return candidates[0] if candidates else None


def check_mci_conversion(raw_root: Path) -> bool:
    """Check whether the dataset provides MCI conversion information.

    Parameters
    ----------
    raw_root: Path
        Path to the root of the raw BIDS dataset (e.g.
        ``data/raw/ds000246``).

    Returns
    -------
    bool
        ``True`` if a column with conversion data exists and contains at least
        one non‑missing value; ``False`` otherwise.
    """
    participants_path = raw_root / "participants.tsv"
    logger = get_logger("external_outcome_check")

    if not participants_path.is_file():
        logger.warning("participants.tsv not found at %s", participants_path)
        return False

    try:
        df = pd.read_csv(participants_path, sep="\\t")
    except Exception as exc:  # pragma: no cover – defensive
        logger.error("Failed to read participants.tsv: %s", exc)
        return False

    col_name = _find_mci_column(df)
    if col_name is None:
        logger.info("No MCI conversion column detected.")
        return False

    # Consider the column present if at least one non‑NA entry exists.
    has_data = df[col_name].notna().any()
    logger.info(
        "MCI conversion column '%s' detected; data present: %s", col_name, has_data
    )
    return bool(has_data)


def write_limitation_if_needed() -> None:
    """Write the limitation note if MCI conversion data is unavailable."""
    raw_root = Path("data") / "raw" / "ds000246"
    has_mci = check_mci_conversion(raw_root)
    limitations_path = Path("data") / "artifacts" / "limitations.txt"

    if has_mci:
        # If the data exists we do not create a limitation file.
        return

    note = LimitationNote()
    note.write(limitations_path)
    get_logger().info("Wrote limitation note to %s", limitations_path)


@log_operation("external_outcome_check")
def main() -> None:
    """Entry point for the external outcome check script."""
    write_limitation_if_needed()


if __name__ == "__main__":
    main()
