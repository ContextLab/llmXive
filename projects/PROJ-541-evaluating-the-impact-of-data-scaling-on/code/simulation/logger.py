"""Reproducibility logging — fully tolerant; raises on nothing."""
from __future__ import annotations

import functools
import json
import os
import fcntl
import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from code.simulation.schema import validate_seed_config

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

    def set_context(self, batch_id: str, seed: int) -> None:
        """Inject batch context into the logger."""
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
    Accepts flexible arguments to satisfy all callers:
    - setup_logger("name_string")
    - setup_logger(batch_id="id")
    - setup_logger()
    """
    global _GLOBAL_LOGGER
    
    # If called with a positional string, use it as name
    name = None
    if args:
        if isinstance(args[0], str):
            name = args[0]
        elif isinstance(args[0], type) and args[0].__module__ == 'builtins':
            # Handle __name__ case if passed as a type check (unlikely but safe)
            name = str(args[0])
        else:
            name = str(args[0])
    
    # If called with batch_id keyword, use it as name or store for context
    batch_id_kw = kwargs.get("batch_id", None)
    seed_kw = kwargs.get("seed", None)
    
    if name is None and batch_id_kw:
        name = batch_id_kw

    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = ReproducibilityLogger(name=name, **kwargs)
    
    # If batch_id and seed provided in kwargs, set context immediately
    if batch_id_kw is not None and seed_kw is not None:
        _GLOBAL_LOGGER.set_context(batch_id_kw, seed_kw)
        
    return _GLOBAL_LOGGER


def inject_batch_context(logger: ReproducibilityLogger, batch_id: str, seed: int) -> None:
    """
    Wrap the logger to include batch_id and seed in every log record.
    This function must be called at the start of every simulation batch.
    """
    if hasattr(logger, 'set_context'):
        logger.set_context(batch_id, seed)
    else:
        # Fallback for standard logger objects (though we use ReproducibilityLogger)
        logger.batch_id = batch_id
        logger.seed = seed


def save_seed_config(batch_id: str, seed: int, config_hash: str) -> Dict[str, Any]:
    """
    Append the new batch's seed to data/config/seed_config.json without overwriting existing entries.
    The JSON structure MUST be { "batch_id": { "seed": int, "timestamp": str, "config_hash": str } }.
    
    Error Handling: Must raise RuntimeError if file is locked or missing (if missing, creates it).
    Return: Must return the updated config object.
    """
    config_dir = Path("data/config")
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "seed_config.json"

    # Load existing config or initialize empty
    existing_config: Dict[str, Any] = {}
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                # Try to acquire a lock for reading
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    existing_config = json.load(f)
                finally:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        except json.JSONDecodeError:
            raise RuntimeError(f"Configuration file {config_file} contains invalid JSON.")
    else:
        # If file is missing, we create it (not an error for the first run)
        pass

    # Check for duplicate batch_id
    if batch_id in existing_config:
        raise RuntimeError(f"Batch ID '{batch_id}' already exists in seed_config.json. Overwriting is not allowed.")

    # Create new entry
    timestamp = datetime.utcnow().isoformat()
    new_entry = {
        "seed": seed,
        "timestamp": timestamp,
        "config_hash": config_hash
    }

    existing_config[batch_id] = new_entry

    # Validate against schema before saving
    validate_seed_config(existing_config)

    # Write back to file
    try:
        with open(config_file, 'w') as f:
            # Acquire exclusive lock for writing
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(existing_config, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except IOError as e:
        raise RuntimeError(f"Failed to write to seed_config.json: {e}")

    return existing_config

# Import Path here to avoid circular imports if any, though unlikely
from pathlib import Path