"""
Reproducibility logging utilities.

This module provides a lightweight logging system used throughout the
project.  It records operations, input/output files, parameters, status,
and timing information to a JSON lines file (``logs.json``) located in the
``data/logs`` directory.  The implementation is deliberately permissive:
``log_operation`` accepts arbitrary keyword arguments so that existing
scripts can pass any combination of ``input_file``, ``output_file``,
``output_files``, ``logger`` etc. without raising ``TypeError``.
"""

import json
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "logs.jsonl"


@dataclass
class LogEntry:
    """A single log entry for a reproducibility operation."""

    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    operation: str = ""
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    # ``output_files`` can be a list or a single string; we store the JSON
    # representation so that downstream tools can parse it uniformly.
    output_files: Optional[Any] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "success"
    duration_ms: Optional[int] = None

    def to_json(self) -> str:
        """Serialise the entry to a single‑line JSON string."""
        # ``asdict`` recursively converts dataclass fields.
        return json.dumps(asdict(self), ensure_ascii=False)


class ReproducibilityLogger:
    """
    Simple logger that writes ``LogEntry`` objects to ``data/logs/logs.jsonl``.
    It mimics the subset of the standard ``logging.Logger`` API that the
    project uses (currently only ``info`` is required).
    """

    def __init__(self, name: str = "reproducibility"):
        self.name = name
        self.log_path = LOG_PATH

    def _write(self, entry: LogEntry) -> None:
        """Append a JSON line to the log file."""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(entry.to_json() + "\n")

    def info(self, message: str, **kwargs: Any) -> None:
        """
        Record an informational message.

        ``message`` is stored in the ``operation`` field; any additional
        keyword arguments are stored in ``parameters``.
        """
        entry = LogEntry(operation=message, parameters=kwargs)
        self._write(entry)

    # Additional logging levels can be added later if needed.


_global_logger: Optional[ReproducibilityLogger] = None


def get_logger() -> ReproducibilityLogger:
    """
    Return a singleton ``ReproducibilityLogger`` instance.
    The first call creates the logger; subsequent calls return the same
    instance, ensuring all scripts write to the same log file.
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = ReproducibilityLogger()
    return _global_logger


def log_operation(
    *,
    operation: str,
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
    output_files: Optional[Any] = None,
    logger: Optional[ReproducibilityLogger] = None,
    **parameters: Any,
) -> LogEntry:
    """
    Record an operation in the reproducibility log.

    The function is deliberately tolerant of extra keyword arguments.
    Callers may supply any subset of the documented parameters as well as
    additional custom fields; they will be captured verbatim in the
    ``parameters`` dictionary of the resulting ``LogEntry``.

    Returns the ``LogEntry`` instance for optional downstream use.
    """
    start = time.time()
    entry = LogEntry(
        operation=operation,
        input_file=input_file,
        output_file=output_file,
        output_files=output_files,
        parameters=parameters,
    )
    # If a logger instance is supplied, use its ``info`` method to also
    # emit a human‑readable line.  This mirrors the previous behaviour of
    # the project where scripts passed ``logger=`` to the helper.
    if logger is not None:
        logger.info(operation, **parameters)

    # Record duration.
    entry.duration_ms = int((time.time() - start) * 1000)
    # Persist the entry.
    get_logger()._write(entry)
    return entry
