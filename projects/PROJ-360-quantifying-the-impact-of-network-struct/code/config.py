"""
Configuration manager for the project.

This module defines a singleton ``Config`` class that loads configuration
values from environment variables, provides convenient accessors, and
supplies a fixed random‑seed dictionary for deterministic behaviour across
libraries.

The original implementation expected the Materials Project API key to be
provided via the ``MP_API_KEY`` environment variable.  The specification
requires the key to be read from ``MATERIALS_PROJECT_API_KEY``.  To maintain
backward compatibility with existing scripts (which still query
``MP_API_KEY``), the loader now checks both variables and stores the value
under both keys.

The ``initialize_environment`` helper now returns the ``Config`` instance
(instead of ``None``) so callers that expect a configuration object (e.g.
``download.py``) continue to work.
"""

import os
import random
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class Config:
    """Singleton configuration manager."""

    _instance = None
    _config_data: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Prevent re‑initialisation on subsequent calls
        if getattr(self, "_initialized", False):
            return
        self._initialized = True
        self._load_config()

    # ------------------------------------------------------------------
    # Loading configuration
    # ------------------------------------------------------------------
    def _load_config(self):
        """
        Populate the internal dictionary from environment variables.

        Keys:
            MP_API_KEY / MATERIALS_PROJECT_API_KEY
                API key for the Materials Project.  Both names are accepted;
                the value is stored under both keys for compatibility.
            RANDOM_SEED
                Integer seed for deterministic randomness.  Defaults to 42.
            LOG_LEVEL
                Logging level name (e.g. "INFO").
            DATA_DIR, CODE_DIR, RESULTS_DIR, MODELS_DIR
                Directory locations used throughout the project.
        """
        # API key – accept both the historic and the spec‑required name
        mp_key = os.getenv("MP_API_KEY") or os.getenv("MATERIALS_PROJECT_API_KEY", "")
        self._config_data = {
            "MP_API_KEY": mp_key,
            "MATERIALS_PROJECT_API_KEY": mp_key,
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "DATA_DIR": os.getenv("DATA_DIR", "data"),
            "CODE_DIR": os.getenv("CODE_DIR", "code"),
            "RESULTS_DIR": os.getenv("RESULTS_DIR", "results"),
            "MODELS_DIR": os.getenv("MODELS_DIR", "models"),
        }

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value."""
        return self._config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set or override a configuration value."""
        self._config_data[key] = value

    def get_random_seed(self) -> int:
        """Return the primary random seed."""
        return self._config_data.get("RANDOM_SEED", 42)

    def get_random_seed_dict(self) -> Dict[str, int]:
        """
        Return a dictionary of deterministic seeds for common libraries.

        This dictionary can be passed to downstream utilities that expect a
        mapping of library names to seeds.
        """
        seed = self.get_random_seed()
        return {
            "python_random": seed,
            "numpy": seed,
            # Extend with other libraries if needed (e.g. torch, tensorflow)
        }

    def get_api_key(self) -> str:
        """Convenient accessor for the Materials Project API key."""
        return self._config_data.get("MP_API_KEY", "")

    # ------------------------------------------------------------------
    # Compatibility shim for logger‑style attribute access
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Any undefined attribute (commonly logger methods such as
        ``info``/``debug``/``warning``) resolves to a no‑op callable.
        This prevents ``AttributeError`` in scripts that treat the Config
        instance like a logger.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def get_config() -> Config:
    """Return the singleton Config instance."""
    return Config()

def reset_config() -> None:
    """Reset the singleton (useful for isolated tests)."""
    Config._instance = None
    Config._config_data = {}

def initialize_environment() -> Config:
    """
    Initialise the runtime environment:

    * Seed the built‑in ``random`` module and NumPy (if available) with the
      deterministic seed from the configuration.
    * Set the global logging level according to ``LOG_LEVEL``.
    * Return the ``Config`` instance for callers that expect it.

    Returns
    -------
    Config
        The singleton configuration object.
    """
    config = get_config()

    # Seed the standard library RNG
    seed = config.get_random_seed()
    random.seed(seed)

    # Seed NumPy if it is importable
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:  # pragma: no cover – NumPy is always available in the env
        pass

    # Configure root logger level
    log_level_name = config.get("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level_name, logging.INFO)
    logging.basicConfig(level=numeric_level)
    logger = logging.getLogger(__name__)
    logger.info(f"Environment initialised with seed {seed} and log level {log_level_name}")

    return config

def main():
    """Simple sanity‑check entry point."""
    cfg = get_config()
    print(f"MP_API_KEY: {cfg.get('MP_API_KEY', 'Not set')}")
    print(f"RANDOM_SEED: {cfg.get_random_seed()}")
    print(f"LOG_LEVEL: {cfg.get('LOG_LEVEL')}")
    print(f"Random seed dict: {cfg.get_random_seed_dict()}")

if __name__ == "__main__":
    main()