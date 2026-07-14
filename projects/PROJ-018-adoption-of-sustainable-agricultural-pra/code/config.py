"""Configuration handling for the project.

Provides a flexible ``get_config`` helper that can be used in two ways:

1. ``get_config()`` – returns a ``Config`` instance.
2. ``get_config("key", default)`` – returns the value for ``key`` (or ``default``).

The ``Config`` class also offers a ``get`` method for dictionary‑style access
and tolerates any unknown attribute access by returning a no‑op callable.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

_GLOBAL_CONFIG: Dict[str, Any] | None = None
_CONFIG_PATH: Path | None = None


class ConfigError(RuntimeError):
    """Raised for configuration‑related problems."""


class Config:
    """A thin wrapper around the underlying configuration dictionary."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self._data = data

    # ------------------------------------------------------------------
    # Dictionary‑style accessor used throughout the codebase.
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    # ------------------------------------------------------------------
    # Mutating helpers – not required for the current pipeline but kept
    # for completeness.
    # ------------------------------------------------------------------
    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    # ------------------------------------------------------------------
    # Graceful fallback for any attribute that scripts might call
    # (e.g. ``config.info(...)``). Returns a no‑op callable.
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        def _noop(*_a: Any, **_kw: Any) -> None:
            return None

        return _noop

    # ------------------------------------------------------------------
    # Serialise back to JSON if needed.
    # ------------------------------------------------------------------
    def to_json(self) -> str:
        return json.dumps(self._data, ensure_ascii=False, indent=2)


def _load_config_file(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise ConfigError(f"Failed to read config file {path}: {exc}") from exc


def _initialize_global_config() -> None:
    """Populate the module‑level ``_GLOBAL_CONFIG`` dictionary."""
    global _GLOBAL_CONFIG, _CONFIG_PATH
    if _GLOBAL_CONFIG is not None:
        return

    # Determine the config file location – default to ``code/config.yaml``.
    default_path = Path(__file__).with_name("config.yaml")
    config_path = Path(os.getenv("PROJECT_CONFIG_PATH", default_path))
    _CONFIG_PATH = config_path
    _GLOBAL_CONFIG = _load_config_file(config_path)

    # Apply a deterministic random seed if one is provided.
    seed = _GLOBAL_CONFIG.get("random_seed")
    if isinstance(seed, int):
        set_random_seed(seed)


def get_config(*args: Any, **kwargs: Any) -> Any:
    """
    Flexible accessor.

    * ``get_config()`` → returns a ``Config`` instance.
    * ``get_config("key", default)`` → returns the value for ``key``.
    """
    _initialize_global_config()
    assert _GLOBAL_CONFIG is not None  # for type‑checkers

    # No positional arguments → return the Config wrapper.
    if not args:
        return Config(_GLOBAL_CONFIG)

    # First argument is a string → treat as key lookup.
    if isinstance(args[0], str):
        key = args[0]
        default = args[1] if len(args) > 1 else None
        return _GLOBAL_CONFIG.get(key, default)

    # Fallback – return the Config object.
    return Config(_GLOBAL_CONFIG)


def set_config(key: str, value: Any) -> None:
    """Update a config value and persist it back to disk."""
    _initialize_global_config()
    assert _GLOBAL_CONFIG is not None
    _GLOBAL_CONFIG[key] = value
    if _CONFIG_PATH is not None:
        _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _CONFIG_PATH.open("w", encoding="utf-8") as f:
            json.dump(_GLOBAL_CONFIG, f, indent=2)


def set_random_seed(seed: int) -> None:
    """Seed the Python, NumPy and random modules for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except Exception:
        pass  # NumPy may not be installed – ignore safely.


# Helper shortcuts used by many scripts ---------------------------------
def get_config_path() -> Path:
    return Path(get_config("project_root", "."))


def get_data_path() -> Path:
    return get_config_path() / get_config("data_path", "data")


def get_raw_data_path() -> Path:
    return get_data_path() / get_config("raw_data_path", "raw")


def get_processed_data_path() -> Path:
    return get_data_path() / get_config("processed_data_path", "processed")


def get_results_path() -> Path:
    return get_config_path() / get_config("results_path", "results")


def get_modeling_log_path() -> Path:
    return get_config_path() / get_config("modeling_log_path", "modeling_log.yaml")
