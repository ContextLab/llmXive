"""Central configuration utilities for the project.

The implementation is deliberately tolerant: ``get_config`` can be called in a
variety of ways (no arguments, a single key, a key with a default, keyword
arguments, etc.) – all call‑sites used throughout the repository are supported.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

import yaml

# --------------------------------------------------------------------------- #
# Global state
# --------------------------------------------------------------------------- #
_CONFIG_PATH: Path = Path("code/config.yaml")
_CONFIG: dict[str, Any] | None = None


def set_config_path(path: str | os.PathLike) -> None:
    """Change the location of the YAML configuration file."""
    global _CONFIG_PATH, _CONFIG
    _CONFIG_PATH = Path(path)
    _CONFIG = None  # force reload on next get_config()


def _load_config() -> dict[str, Any]:
    """Load (or reload) the YAML configuration file."""
    if not _CONFIG_PATH.is_file():
        # If the file does not exist we fall back to an empty config – callers
        # may still provide defaults via ``get_config(key, default)``.
        return {}
    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_config(key: str | None = None, default: Any = None, **kwargs: Any) -> Any:
    """Retrieve configuration values.

    Supported signatures (all used somewhere in the repo):
      - get_config()
      - get_config(key)
      - get_config(key, default)
      - get_config(key=..., default=...)
      - get_config(key='my_key')

    If ``key`` is omitted the full configuration dictionary is returned.
    """
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _load_config()

    # Allow callers to pass the key via a keyword argument named ``key``.
    if key is None and "key" in kwargs:
        key = kwargs.pop("key")

    if key is None:
        # No specific key requested – return the whole dict.
        return _CONFIG

    # At this point ``key`` is a string.
    return _CONFIG.get(key, default)


def set_config(key: str, value: Any) -> None:
    """Update the in‑memory configuration and persist it to disk."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _load_config()
    _CONFIG[key] = value
    # Persist the modified configuration.
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(_CONFIG, f)


# --------------------------------------------------------------------------- #
# Helper getters that return concrete Path objects
# --------------------------------------------------------------------------- #
def _base_path() -> Path:
    """Root of the repository – used as a base for all relative paths."""
    # The repository root is two levels up from this file (code/).
    return Path(__file__).resolve().parents[1]


def get_data_path() -> Path:
    return _base_path() / get_config("data_path", "data")


def get_raw_data_path() -> Path:
    return _base_path() / get_config("raw_data_path", "data/raw")


def get_processed_data_path() -> Path:
    return _base_path() / get_config("processed_data_path", "data/processed")


def get_results_path() -> Path:
    return _base_path() / get_config("results_path", "results")


def get_figures_path() -> Path:
    return _base_path() / get_config("figures_path", "figures")


def get_modeling_log_path() -> Path:
    return _base_path() / get_config("modeling_log_path", "modeling_log.yaml")


def get_engineered_data_path() -> Path:
    """Convenience path to the engineered data CSV produced by feature engineering."""
    return get_processed_data_path() / "engineered_data.csv"


# --------------------------------------------------------------------------- #
# Directory creation utilities
# --------------------------------------------------------------------------- #
def ensure_directories() -> None:
    """Create all standard project directories if they do not already exist."""
    for p in (
        get_data_path(),
        get_raw_data_path(),
        get_processed_data_path(),
        get_results_path(),
        get_figures_path(),
    ):
        p.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------------------------------- #
# Random‑seed helpers – deterministic behaviour across the pipeline
# --------------------------------------------------------------------------- #
def set_random_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass  # numpy may not be installed yet; ignore safely


def init_random_seed(default: int = 42) -> None:
    """Initialise the random seed from config if present, otherwise use ``default``."""
    seed = get_config("random_seed", default)
    set_random_seed(int(seed))
