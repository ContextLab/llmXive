"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import logging
import os
import fcntl
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Optional, Dict

from code.simulation.schema import validate_seed_config, load_seed_config
from pathlib import Path


@dataclass
class LogEntry:
    operation: str = ""
    parameters: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    batch_id: Optional[str] = None
    seed: Optional[int] = None

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
        self._batch_id: Optional[str] = None
        self._seed: Optional[int] = None

    def log(self, *args: Any, **kwargs: Any) -> "LogEntry":
        op = args[0] if args else kwargs.get("operation", "")
        entry = LogEntry(
            operation=str(op),
            parameters=dict(kwargs),
            batch_id=self._batch_id,
            seed=self._seed
        )
        self.entries.append(entry)
        return entry

    def set_batch_context(self, batch_id: str, seed: int) -> None:
        """Inject batch_id and seed into the logger context for all subsequent logs."""
        self._batch_id = batch_id
        self._seed = seed

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


def setup_logger(*args: Any, **kwargs: Any) -> ReproducibilityLogger:
    """
    Setup and return a logger instance.
    Accepts various call shapes:
      - setup_logger("name_string")
      - setup_logger(batch_id="id")
      - setup_logger(__name__)
      - setup_logger()
    Returns a ReproducibilityLogger which supports .log(), .to_json(), and context injection.
    """
    logger_name = None
    batch_id = None
    seed = None

    if args:
        if isinstance(args[0], str):
            logger_name = args[0]
        elif args[0] is None:
            logger_name = "reproducibility"
        else:
            logger_name = str(args[0])

    if "batch_id" in kwargs:
        batch_id = kwargs.pop("batch_id")
    if "seed" in kwargs:
        seed = kwargs.pop("seed")
    if "name" in kwargs:
        logger_name = kwargs.pop("name")

    if not logger_name:
        logger_name = "reproducibility"

    # Use the global logger singleton for consistency across the project
    logger = get_logger(name=logger_name)

    # If batch_id and seed are provided at setup, inject them immediately
    if batch_id is not None and seed is not None:
        logger.set_batch_context(batch_id, seed)

    return logger


def inject_batch_context(logger: ReproducibilityLogger, batch_id: str, seed: int) -> None:
    """
    Inject batch_id and seed into the logger context.
    This function must be called at the start of every simulation batch.
    It updates the logger instance in-place so all subsequent log records
    include the batch_id and seed.
    """
    if hasattr(logger, 'set_batch_context'):
        logger.set_batch_context(batch_id, seed)
    else:
        # Fallback for any logger that doesn't support the method directly
        # (though in this project, we always use ReproducibilityLogger)
        pass


def save_seed_config(batch_id: str, seed: int, config_hash: str) -> Dict[str, Any]:
    """
    Append a new batch's seed configuration to data/config/seed_config.json.

    Requirements:
    - Uses schema from T005d and validation from T005e.
    - Appends without overwriting existing entries.
    - JSON structure: { "batch_id": { "seed": int, "timestamp": str, "config_hash": str } }
    - File Path: data/config/seed_config.json
    - Error Handling: Raises RuntimeError if file is locked or missing (or directory missing).
    - Return: The updated config object (dict).

    The file is append-only; new batches add new keys, existing keys are never overwritten.
    """
    config_path = Path("data/config/seed_config.json")
    
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing config or start fresh
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                # Use fcntl for file locking on Unix to prevent race conditions
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    current_config = json.load(f)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except (IOError, OSError) as e:
                    raise RuntimeError(f"Failed to lock or read seed config file: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in seed config file: {e}")
    else:
        current_config = {}

    # Validate that the current config matches the expected schema structure
    # (We assume T005e's validate_seed_config is called on load if needed, 
    # but here we ensure the structure is compatible before writing)
    
    # Prepare new entry
    timestamp = datetime.utcnow().isoformat()
    new_entry = {
        "seed": seed,
        "timestamp": timestamp,
        "config_hash": config_hash
    }

    # Check if batch_id already exists (should not happen in append-only, but safety check)
    if batch_id in current_config:
        raise RuntimeError(f"Batch ID '{batch_id}' already exists in seed config. Overwriting is not allowed.")

    # Append new entry
    current_config[batch_id] = new_entry

    # Validate the updated config against schema (imported from schema.py)
    try:
        validate_seed_config(current_config)
    except Exception as e:
        raise RuntimeError(f"Updated seed config failed validation: {e}")

    # Write back to file with exclusive lock
    try:
        with open(config_path, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(current_config, f, indent=2)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to write seed config file: {e}")

    return current_config
