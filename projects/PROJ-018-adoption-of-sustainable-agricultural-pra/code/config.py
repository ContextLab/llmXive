"""Configuration handling for the project.

The module provides a flexible ``get_config`` function that can be called
with zero, one or two positional arguments and also with keyword arguments.
All other helper functions (path getters, random‑seed utilities, etc.) are
retained from the original implementation.
"""
from __future__ import annotations

import json
import os
import random
import yaml
from pathlib import Path
from typing import Any, Dict

# ----------------------------------------------------------------------
# Internal state
# ----------------------------------------------------------------------
_CONFIG_PATH: Path | None = None
_CONFIG: Dict[str, Any] = {}


def _load_config_file(path: Path) -> Dict[str, Any]:
    """Load a JSON/YAML configuration file if it exists."""
    if not path.is_file():
        return {}
    try:
        # Prefer JSON – the original project used JSON for its config.
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Fall back to a very simple YAML parser if JSON fails.
        try:
            import yaml  # type: ignore
            with path.open("r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}


def set_config_path(path: str | os.PathLike) -> None:
    """Define a custom path for the configuration file and reload it."""
    global _CONFIG_PATH, _CONFIG
    _CONFIG_PATH = Path(path)
    _CONFIG = _load_config_file(_CONFIG_PATH)


def _ensure_config_loaded() -> None:
    """Make sure the configuration dictionary is populated."""
    global _CONFIG, _CONFIG_PATH
    if _CONFIG:
        return
    # Default location – ``code/config.yaml`` relative to this file.
    default_path = Path(__file__).with_name("config.yaml")
    _CONFIG_PATH = _CONFIG_PATH or default_path
    _CONFIG = _load_config_file(_CONFIG_PATH)


# ----------------------------------------------------------------------
# Public API – flexible ``get_config``
# ----------------------------------------------------------------------
def get_config(*args: Any, **kwargs: Any) -> Any:
    """

    Supported call signatures:

    * ``get_config()`` → returns the whole configuration dict.
    * ``get_config(key)`` → returns the value for *key* or ``None``.
    * ``get_config(key, default)`` → returns the value or *default*.
    * ``get_config(key=..., default=...)`` → same as above.
    * ``get_config(key='my_key')`` → value or ``None``.

    The function never raises – missing keys simply result in ``None``
    (or the supplied default).
    """
    _ensure_config_loaded()
    # No positional arguments → return the whole config.
    if not args and not kwargs:
        return _CONFIG

    # Extract key and default from positional or keyword arguments.
    key: str | None = None
    default: Any = None

    if args:
        key = str(args[0])
        if len(args) > 1:
            default = args[1]
    if "key" in kwargs:
        key = str(kwargs["key"])
    if "default" in kwargs:
        default = kwargs["default"]

    if key is None:
        return _CONFIG

    return _CONFIG.get(key, default)

def set_config(key: str, value: Any) -> None:
    """Set a configuration key in the singleton (in‑memory only)."""
    cfg = init_config()
    cfg._data[key] = value

# ----------------------------------------------------------------------
# Helper getters – they delegate to ``get_config`` for flexibility.
# ----------------------------------------------------------------------
def get_data_path() -> Path:
    return Path(get_config("data_path", "data"))


def get_raw_data_path() -> Path:
    return Path(get_config("raw_data_path", "data/raw"))


def get_processed_data_path() -> Path:
    return Path(get_config("processed_data_path", "data/processed"))


def get_results_path() -> Path:
    return Path(get_config("results_path", "results"))


def get_figures_path() -> Path:
    return Path(get_config("figures_path", "figures"))


def get_modeling_log_path() -> Path:
    return Path(get_config("modeling_log_path", "modeling_log.yaml"))


def get_engineered_data_path() -> Path:
    """Convenience path for the engineered dataset."""
    return get_processed_data_path() / "engineered_data.csv"


def ensure_directories() -> None:
    """Create all standard project directories if they do not exist."""
    for p in (
        get_data_path(),
        get_raw_data_path(),
        get_processed_data_path(),
        get_results_path(),
        get_figures_path(),
    ):
        p.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------------------
# Random‑seed utilities (used throughout the pipeline)
# ----------------------------------------------------------------------
def set_random_seed(seed: int) -> None:
    """Set the global random seed for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass


def init_random_seed() -> int:
    """Initialise a seed from the config or generate a new one."""
    seed = get_config("random_seed")
    if seed is None:
        seed = random.randint(0, 2**31 - 1)
        set_random_seed(seed)
        # Persist the generated seed back to the config file for future runs.
        if _CONFIG_PATH and _CONFIG_PATH.is_file():
            try:
                with _CONFIG_PATH.open("r+", encoding="utf-8") as f:
                    cfg = json.load(f)
                    cfg["random_seed"] = seed
                    f.seek(0)
                    json.dump(cfg, f, indent=2)
                    f.truncate()
            except Exception:
                pass
    else:
        set_random_seed(int(seed))
    return int(seed)
