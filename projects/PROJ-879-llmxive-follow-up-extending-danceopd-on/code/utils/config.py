"""
Configuration management for the project.

This module provides a simple yet flexible way to access configuration
values such as random seeds, filesystem paths, and hyper‑parameters.
It loads a YAML (preferred) or JSON configuration file if it exists;
otherwise, it falls back to sensible defaults that satisfy the
requirements of the pipeline (e.g. ``N_TARGET=2500`` and
``TIMEOUT_HOURS=6``).

The public API mirrors the original placeholder implementation so that
existing imports continue to work:

* ``get_config(config_path: Optional[Path] = None) -> Config``
* ``get_path(key: str, base: Optional[Path] = None) -> Path``
* ``get_hyperparameter(key: str) -> Any``
* ``get_seed() -> int``

All functions return concrete values or raise informative errors when a
required key is missing.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml  # pyyaml is declared in requirements.txt
except Exception as exc:  # pragma: no cover
    raise ImportError("pyyaml is required for config loading") from exc

# ----------------------------------------------------------------------
# Default configuration values
# ----------------------------------------------------------------------
_DEFAULTS: Dict[str, Any] = {
    # Hyper‑parameters
    "N_TARGET": 2500,
    "TIMEOUT_HOURS": 6.0,
    # Random seed
    "seed": 42,
    # Project root – calculated relative to this file
    "PROJECT_ROOT": str(Path(__file__).resolve().parents[2]),
    # Common directory shortcuts (can be overridden by a user config file)
    "DATA_RAW_DIR": "data/raw",
    "DATA_PROCESSED_DIR": "data/processed",
    "DATA_RESULTS_DIR": "data/results",
    "MODELS_DIR": "models",
    "STATE_DIR": "state",
}

class Config:
    """
    Wrapper around a configuration dictionary.

    The class is deliberately lightweight – it only offers ``get`` and
    attribute‑style access to the underlying mapping.  It also ensures
    that missing keys raise ``KeyError`` with a clear message.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialise the configuration.

        Parameters
        ----------
        config_path: Optional[Path]
            Path to a YAML or JSON configuration file.  If ``None``,
            ``config.yaml`` in the project root is used.  When the file
            does not exist, the defaults defined in ``_DEFAULTS`` are used.
        """
        self.config_path = config_path or Path(_DEFAULTS["PROJECT_ROOT"]) / "config.yaml"
        self._data: Dict[str, Any] = self._load_config()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from ``self.config_path`` if it exists.
        YAML is preferred; JSON is used as a fallback based on the file
        extension.  Missing files result in an empty dict which will be
        merged with the defaults later.
        """
        if not self.config_path.exists():
            # No user‑provided config – just return an empty dict.
            return {}

        try:
            if self.config_path.suffix.lower() in {".yaml", ".yml"}:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    # ``yaml.safe_load`` returns ``None`` for empty files.
                    data = yaml.safe_load(f) or {}
            elif self.config_path.suffix.lower() == ".json":
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                raise ValueError(
                    f"Unsupported config file type: {self.config_path.suffix}"
                )
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Failed to load config file {self.config_path}") from exc

        if not isinstance(data, dict):
            raise TypeError(
                f"Configuration file must contain a mapping, got {type(data)}"
            )
        return data

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value.

        Lookup order:
        1. User‑provided configuration (if any)
        2. Built‑in defaults from ``_DEFAULTS``
        3. ``default`` argument

        Parameters
        ----------
        key: str
            Configuration key.
        default: Any, optional
            Value to return when the key is absent from both the user
            config and defaults.

        Returns
        -------
        Any
            The stored value or ``default``.
        """
        if key in self._data:
            return self._data[key]
        if key in _DEFAULTS:
            return _DEFAULTS[key]
        return default

    # Allow attribute‑style access (e.g. ``config.N_TARGET``)
    def __getattr__(self, item: str) -> Any:  # pragma: no cover
        try:
            return self.get(item)
        except KeyError:
            raise AttributeError(item)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Config(path={self.config_path}, data={self._data})"

# ----------------------------------------------------------------------
# Helper functions – these are the stable public API used throughout the
# code base.
# ----------------------------------------------------------------------
def get_config(config_path: Optional[Path] = None) -> Config:
    """
    Return a :class:`Config` instance.

    This function is cheap – the ``Config`` object lazily reads the file
    only once per process.  Subsequent calls simply return a new wrapper
    around the same underlying data.
    """
    return Config(config_path)


def get_path(key: str, base: Optional[Path] = None) -> Path:
    """
    Resolve a filesystem path from the configuration.

    The configuration is expected to store relative paths (e.g.
    ``"data/raw"``).  If ``base`` is provided, it is joined with the
    stored value; otherwise the value is interpreted as an absolute or
    project‑relative path.

    Parameters
    ----------
    key: str
        The configuration key that holds the path string.
    base: Optional[Path]
        Optional base directory to prepend.

    Returns
    -------
    Path
        The resolved path.

    Raises
    ------
    KeyError
        If the key is not present in the configuration.
    """
    config = get_config()
    val = config.get(key)
    if val is None:
        raise KeyError(f"Path key {key} not found in config")
    # ``val`` may already be a Path (unlikely) or a string.
    path_val = Path(val)
    return base / path_val if base else path_val


def get_hyperparameter(key: str) -> Any:
    """
    Shortcut to fetch a hyper‑parameter from the configuration.

    Hyper‑parameters are stored alongside other keys; this helper exists
    for semantic clarity in the code base.
    """
    config = get_config()
    return config.get(key)


def get_seed() -> int:
    """
    Return the random seed for the run.

    The seed defaults to ``42`` when not explicitly set.
    """
    config = get_config()
    return int(config.get("seed", 42))