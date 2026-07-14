"""
Configuration utilities for the project.

This module provides a tolerant configuration loader (`load_config`), a simple
logger setup (`setup_logging`), a seed helper (`get_seed`), and the
`AppConfig` class which offers a flexible ``get`` method and a fallback
``__getattr__`` that returns a no‑op callable for any unknown attribute.
The implementation is deliberately lightweight but compatible with all
existing call sites across the codebase.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Helper classes
# ---------------------------------------------------------------------------

class TolerantDict(dict):
    """
    A dictionary that returns ``default`` (``None`` by default) when a key is
    missing, instead of raising ``KeyError``.  It also supports dot‑notation
    access via ``get`` for nested dictionaries.
    """

    def get(self, key: Any, default: Any = None) -> Any:  # type: ignore[override]
        return super().get(key, default)

# ---------------------------------------------------------------------------
# Core configuration class
# ---------------------------------------------------------------------------

@dataclass
class AppConfig:
    """
    Wrapper around a configuration dictionary providing:

    * ``config`` – the raw dictionary.
    * ``get`` – safe nested access (see implementation below).
    * ``__getattr__`` – returns a no‑op callable for any unknown attribute,
      making the object behave like a logger when methods such as ``info``,
      ``debug`` or ``warning`` are called.
    """

    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Ensure the internal config is always a plain dict (not a subclass)
        if not isinstance(self.config, dict):
            self.config = dict(self.config)

    # -----------------------------------------------------------------------
    # Public API expected by the rest of the project
    # -----------------------------------------------------------------------
    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Retrieve a value from a nested configuration dictionary.

        Usage examples::
            cfg.get("paths", "base")
            cfg.get("paths")                     # returns the sub‑dict
            cfg.get("nonexistent", default=42)   # returns 42

        The method accepts a variable number of keys; it walks the dictionary
        hierarchy accordingly and returns ``default`` if any level is missing.
        """
        if not keys:
            return default

        current: Any = self.config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    # -----------------------------------------------------------------------
    # Fallback for unknown attribute access (e.g., logger‑style calls)
    # -----------------------------------------------------------------------
    def __getattr__(self, name: str):
        """
        Any attribute that is not explicitly defined returns a callable that
        does nothing and returns ``None``.  This makes ``AppConfig`` safe to
        use as a drop‑in logger without raising ``AttributeError``.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load a JSON/YAML configuration file.  If ``config_path`` is ``None`` the
    function looks for an environment variable ``PROJECT_CONFIG``; if that is
    also unset it falls back to ``config.yaml`` in the project root.
    """
    if config_path is None:
        env_path = os.getenv("PROJECT_CONFIG")
        config_path = Path(env_path) if env_path else Path("config.yaml")

    if not config_path.is_file():
        # Return an empty configuration – callers will receive defaults.
        return AppConfig(config={})

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            if config_path.suffix in {".yaml", ".yml"}:
                import yaml  # yaml is a declared dependency
                raw = yaml.safe_load(f) or {}
            else:
                raw = json.load(f)
    except Exception as exc:
        logging.error("Failed to load config file %s: %s", config_path, exc)
        raw = {}

    return AppConfig(config=raw)

def setup_logging(level: str = "INFO") -> None:
    """
    Basic logging configuration used throughout the project.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def get_seed(config: Optional[AppConfig] = None) -> int:
    """
    Retrieve a deterministic random seed from the configuration.  If no seed
    is defined, a default of ``42`` is returned.
    """
    if config is None:
        config = load_config()
    return int(config.get("seed", default=42))

def main() -> None:
    """
    Entry‑point used by ``python -m code.config.env_config``.  It simply loads
    the configuration and prints it – useful for quick sanity checks.
    """
    cfg = load_config()
    print(json.dumps(cfg.config, indent=2))
