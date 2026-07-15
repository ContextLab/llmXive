"""
Configuration handling for the project.

This module defines a ``Config`` class that reads configuration values from
environment variables (or a JSON file) and provides sensible defaults for the
core variables required by the pipeline:

- ``DATASET_URLS``: a JSON‑encoded list of URLs to download datasets from.
- ``OUTPUT_PATH``: directory where processed artifacts are written.
- ``RANDOM_SEED``: integer seed used for reproducibility.
- ``BOOTSTRAP_ITERATIONS``: default number of bootstrap resamples.

The class also implements a permissive ``__getattr__`` fallback so that
scripts can call logger‑style methods (e.g. ``config.info(...)``) without
raising ``AttributeError``.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()  # Load .env if present

# ----------------------------------------------------------------------
# Default values for the required configuration keys
# ----------------------------------------------------------------------
DEFAULT_DATASET_URLS: List[str] = []  # No URLs by default; user should set them
DEFAULT_OUTPUT_PATH: str = "data/processed"
DEFAULT_RANDOM_SEED: int = 42
DEFAULT_BOOTSTRAP_ITERATIONS: int = 1000

class Config:
    """
    Simple configuration holder that reads environment variables and an optional
    JSON configuration file. Provides ``get`` for safe look‑ups and properties
    for the core pipeline variables.
    """

    def __init__(self, config_path: Optional[str] = None):
        # Raw storage for all configuration entries
        self._data: Dict[str, Any] = {}

        # Load from a JSON file if a path is supplied
        if config_path and os.path.isfile(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load config file {config_path}: {e}")

        # Overlay environment variables (they take precedence)
        for key, value in os.environ.items():
            self._data[key] = value

        # Ensure required keys have sensible defaults
        self._apply_defaults()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for *key* if present, otherwise *default*."""
        return self._data.get(key, default)

    @property
    def dataset_urls(self) -> List[str]:
        """
        Return the list of dataset URLs.

        The underlying value may be a JSON‑encoded string, a comma‑separated
        string, or already a list.  All cases are normalised to ``list``.
        """
        raw = self._data.get("DATASET_URLS")
        if raw is None:
            return DEFAULT_DATASET_URLS
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            raw = raw.strip()
            # Try JSON first
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            # Fallback to comma‑separated list
            return [url.strip() for url in raw.split(",") if url.strip()]
        # Unexpected type – fall back to default
        return DEFAULT_DATASET_URLS

    @property
    def output_path(self) -> str:
        """Directory where processed outputs should be written."""
        return str(self._data.get("OUTPUT_PATH", DEFAULT_OUTPUT_PATH))

    @property
    def random_seed(self) -> int:
        """Integer seed used for reproducibility."""
        try:
            return int(self._data.get("RANDOM_SEED", DEFAULT_RANDOM_SEED))
        except (ValueError, TypeError):
            return DEFAULT_RANDOM_SEED

    @property
    def bootstrap_iterations(self) -> int:
        """Number of bootstrap iterations to perform."""
        try:
            return int(self._data.get("BOOTSTRAP_ITERATIONS", DEFAULT_BOOTSTRAP_ITERATIONS))
        except (ValueError, TypeError):
            return DEFAULT_BOOTSTRAP_ITERATIONS

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _apply_defaults(self) -> None:
        """
        Populate missing required keys with their defaults.  This method is
        called during initialisation so that ``self._data`` always contains the
        four core entries, even if the user does not provide them.
        """
        self._data.setdefault("DATASET_URLS", json.dumps(DEFAULT_DATASET_URLS))
        self._data.setdefault("OUTPUT_PATH", DEFAULT_OUTPUT_PATH)
        self._data.setdefault("RANDOM_SEED", str(DEFAULT_RANDOM_SEED))
        self._data.setdefault("BOOTSTRAP_ITERATIONS", str(DEFAULT_BOOTSTRAP_ITERATIONS))

    # ------------------------------------------------------------------
    # Fallback for any unknown attribute/method.
    # ------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Return a no‑op callable for any attribute that does not exist.
        This prevents ``AttributeError`` in scripts that expect
        logger‑style methods (e.g., ``config.info(...)``) or future
        configuration helpers.
        """
        def _noop(*args: Any, **kwargs: Any):
            logging.debug(
                f"Config fallback called for missing attribute '{name}' with args={args}, kwargs={kwargs}"
            )
            return None

        return _noop

# ----------------------------------------------------------------------
# Global accessor helpers
# ----------------------------------------------------------------------
_global_config: Optional[Config] = None

def get_config() -> Config:
    """Return a singleton ``Config`` instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def reload_config() -> None:
    """Force re‑loading of configuration (useful in tests)."""
    global _global_config
    _global_config = Config()

def main() -> None:
    """Simple demo when running this module directly."""
    cfg = get_config()
    print(json.dumps(cfg._data, indent=2))

if __name__ == "__main__":
    main()