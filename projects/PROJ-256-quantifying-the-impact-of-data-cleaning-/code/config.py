"""
Configuration management for the project.

This module provides a simple wrapper around environment variables and an optional
JSON configuration file. It defines explicit default values for the four
environment variables required by the pipeline:

- DATASET_URLS:        JSON‑encoded list of dataset download URLs.
- OUTPUT_PATH:         Directory where processed artifacts are written.
- RANDOM_SEED:         Integer seed used for reproducibility.
- BOOTSTRAP_ITERATIONS: Number of bootstrap resamples (default 1000,
                        reduced to 500 for very large datasets).

Scripts import ``get_config`` and use ``config.get(key, default)`` to obtain
configuration values.  Unknown attribute accesses are tolerated via a no‑op
``__getattr__`` implementation, satisfying the shared‑module contract.
"""

import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load a .env file if present – this allows developers to set environment
# variables locally without committing them to the repository.
load_dotenv()

# ---------------------------------------------------------------------------
# Default configuration values.
#
# The defaults are deliberately simple and can be overridden by either:
#   1. A JSON configuration file passed to ``Config(config_path)``.
#   2. Environment variables.
# ---------------------------------------------------------------------------
_DEFAULTS: Dict[str, Any] = {
    # A JSON‑encoded list of URLs.  The actual URLs are defined in the
    # data acquisition scripts; an empty list is a safe fallback.
    "DATASET_URLS": json.dumps(
        [
            # Example URLs – replace or extend via env var or config file.
            "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip",
            "https://archive.ics.uci.edu/ml/machine-learning-databases/00373/Online%20Retail.xlsx",
        ]
    ),
    # Where processed artifacts such as ``baseline_metrics.json`` will be stored.
    "OUTPUT_PATH": "data/processed",
    # Seed for reproducibility – used by ``utils.pin_random_seed`` and any
    # downstream numpy/scipy random generators.
    "RANDOM_SEED": 42,
    # Number of bootstrap iterations; scripts may reduce this automatically
    # for very large datasets (see T045).
    "BOOTSTRAP_ITERATIONS": 1000,
}

class Config:
    """
    Simple configuration wrapper.

    The wrapper first looks for values defined in an optional JSON file,
    then falls back to environment variables, and finally to the module‑wide
    defaults defined above.
    """

    def __init__(self, config_path: Optional[str] = None):
        # Load user‑provided JSON configuration if a path is supplied.
        self._config: Dict[str, Any] = {}
        if config_path and os.path.isfile(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                try:
                    self._config = json.load(f)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON configuration at {config_path}: {exc}"
                    ) from exc

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value.

        Resolution order:
          1. Value present in the JSON config file (if any).
          2. Environment variable with the same name.
          3. Module‑wide default defined in ``_DEFAULTS``.
          4. The ``default`` argument supplied by the caller.

        The method returns the value *as‑is*; callers are responsible for
        casting to the appropriate type (e.g. ``int`` for ``RANDOM_SEED``).
        """
        if key in self._config:
            return self._config[key]

        # Environment variables are always strings; we return them directly
        # and let callers convert if needed.
        env_val = os.getenv(key)
        if env_val is not None:
            return env_val

        if key in _DEFAULTS:
            return _DEFAULTS[key]

        return default

    # ----------------------------------------------------------------------
    # Compatibility shim – many scripts treat the Config instance like a logger.
    # ----------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any undefined attribute (e.g. logger
        methods like ``info``/``warning``).  This satisfies the “shared‑module
        contract” across the code base.
        """
        def _noop(*args, **kwargs):
            return None

        return _noop

# ---------------------------------------------------------------------------
# Global singleton accessor.
# ---------------------------------------------------------------------------
_global_config: Optional[Config] = None

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Return a singleton ``Config`` instance.

    The first call creates the instance; subsequent calls return the same
    object, optionally re‑initialising it if a new ``config_path`` is given.
    """
    global _global_config
    if _global_config is None or config_path is not None:
        _global_config = Config(config_path)
    return _global_config

def reload_config(config_path: Optional[str] = None) -> Config:
    """
    Force a reload of the configuration, discarding any previously cached
    values.  Useful in tests where environment variables may be mutated.
    """
    global _global_config
    _global_config = Config(config_path)
    return _global_config

def main() -> None:
    """Simple sanity‑check when the module is executed directly."""
    cfg = get_config()
    print(json.dumps(cfg._config, indent=2))

# ---------------------------------------------------------------------------
# Exported names – keep the public API stable.
# ---------------------------------------------------------------------------
__all__ = [
    "Config",
    "get_config",
    "reload_config",
    "main",
]