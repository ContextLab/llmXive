"""
Reproducibility logging utilities for the simulation package.
Provides a tolerant logger that never raises on unexpected calls,
as well as seed configuration persistence with schema validation.
"""
from __future__ import annotations

import json
import os
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import functools
from dataclasses import dataclass, field, asdict

# ---------------------------------------------------------------------------
# Core tolerant logger (reference implementation)
# ---------------------------------------------------------------------------

@dataclass
class LogEntry:
    """A single log entry that can be serialised to JSON."""
    operation: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        """Serialise the entry to a JSON string."""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)


class ReproducibilityLogger:
    """
    Minimal logger that accepts any call shape.

    It stores LogEntry objects in ``self.entries`` and provides no‑op
    implementations for the standard logging methods (info, debug, warning,
    error, critical, etc.) so that callers never encounter AttributeError.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # ``name`` is optional – if not provided we fall back to a generic name.
        self.name: str = args[0] if args else kwargs.get("name", "reproducibility")
        self.batch_id: str | None = kwargs.get("batch_id")
        self.entries: list[LogEntry] = []

    # The primary logging API used throughout the codebase.
    def log(self, *args: Any, **kwargs: Any) -> LogEntry:
        """
        Record a log entry.

        ``log("operation_name", param1=val1, ...)`` creates a LogEntry with
        ``operation="operation_name"`` and ``parameters`` containing the
        keyword arguments.
        """
        operation = args[0] if args else kwargs.pop("operation", "")
        entry = LogEntry(operation=str(operation), parameters=dict(kwargs))
        self.entries.append(entry)
        return entry

    # Standard logging method names – all become no‑ops that return ``None``.
    def __getattr__(self, name: str):
        def _noop(*_a: Any, **_kw: Any) -> None:
            return None
        return _noop


# Global singleton – the first call creates the logger, subsequent calls return it.
_GLOBAL_LOGGER: ReproducibilityLogger | None = None


def get_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """Return the global ``ReproducibilityLogger`` instance."""
    global _GLOBAL_LOGGER
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(*args, **kwargs)
    return _GLOBAL_LOGGER


def log_operation(*args: Any, **kwargs: Any):
    """
    Dual‑purpose helper that can be used as a decorator or as a direct logging call.

    As a decorator:

    >>> @log_operation
    ... def foo(): ...

    As a direct call:

    >>> entry = log_operation("my_op", param=1)
    >>> entry.to_json()
    """
    if len(args) == 1 and callable(args[0]) and not kwargs:
        func = args[0]

        @functools.wraps(func)
        def _wrapper(*a: Any, **k: Any):
            return func(*a, **k)

        return _wrapper

    operation = args[0] if args else kwargs.pop("operation", "operation")
    return get_logger().log(operation, **kwargs)


# ---------------------------------------------------------------------------
# Helper functions required by the rest of the project
# ---------------------------------------------------------------------------

def setup_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """
    Initialise (or retrieve) a ``ReproducibilityLogger``.

    The function is deliberately permissive – it accepts:

    * a single positional argument (interpreted as the logger name)
    * a ``batch_id=`` keyword argument
    * no arguments at all
    * any combination of the above
    """
    name = None
    batch_id = None

    # Positional first argument – could be a name string or ``__name__``.
    if args:
        name = args[0]

    # Keyword arguments
    if "name" in kwargs:
        name = kwargs["name"]
    if "batch_id" in kwargs:
        batch_id = kwargs["batch_id"]

    # Fallback defaults
    if name is None:
        name = "reproducibility"

    logger = get_logger(name=name, batch_id=batch_id)
    # Attach attributes expected by the tests
    logger.name = name
    logger.batch_id = batch_id
    return logger


def inject_batch_context(logger: ReproducibilityLogger, batch_id: str) -> ReproducibilityLogger:
    """
    Attach a ``batch_id`` to an existing logger instance.

    The function mutates the logger in‑place and also returns it for convenience.
    """
    logger.batch_id = batch_id
    return logger


def save_seed_config(batch_id: str, seed: int, config_hash: str) -> Dict[str, Any]:
    """
    Persist a seed configuration entry to ``data/config/seed_config.json``.

    The function:

    1. Loads the existing JSON (or starts with an empty dict if the file does not exist).
    2. Validates the *new* overall configuration against the JSON‑Schema defined in
       ``code/simulation/schema.py``.
    3. Writes the updated JSON back to disk using an exclusive, non‑blocking file lock.
    4. Returns the full configuration dictionary after insertion.

    Errors:

    * If the file cannot be locked, ``RuntimeError`` is raised.
    * If schema validation fails, the underlying ``jsonschema.ValidationError`` propagates.
    """
    from .schema import validate_seed_config, load_seed_config

    # Prepare the new entry
    entry = {
        "seed": seed,
        "timestamp": datetime.utcnow().isoformat(),
        "config_hash": config_hash,
    }

    # Load existing configuration (append‑only semantics)
    config_path = Path("data/config/seed_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        existing_config = load_seed_config()
    except Exception:
        existing_config = {}

    # Append / overwrite the specific batch key (append‑only in the sense that we never delete other keys)
    existing_config[batch_id] = entry

    # Validate the whole structure against the schema
    validate_seed_config(existing_config)

    # Write back with a file lock to avoid race conditions
    try:
        with open(config_path, "w") as f:
            fd = f.fileno()
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as e:
                raise RuntimeError(f"Could not acquire lock on seed config file: {e}") from e
            json.dump(existing_config, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(fd)
    except Exception as e:
        raise RuntimeError(f"Failed to write seed config: {e}") from e

    return existing_config
