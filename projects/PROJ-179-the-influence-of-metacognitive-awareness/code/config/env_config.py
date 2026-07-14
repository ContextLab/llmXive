"""
Configuration utilities for the project.

This module provides a tolerant dictionary class, an application configuration
holder with flexible attribute access, and helper functions for loading configuration
files, setting up logging, and retrieving a reproducible random seed.

The implementation is deliberately permissive: any attribute accessed on the
``AppConfig`` instance that is not explicitly defined will return a no‑op callable.
This satisfies the numerous call‑sites that treat the config object like a logger
(e.g. ``config.info(...)``) without raising ``AttributeError``.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

@dataclass
class TolerantDict(dict):
    """
    A thin wrapper around ``dict`` that returns a default value when a key is
    missing, mirroring the behaviour of ``dict.get`` but usable with the
    ``[]`` operator.
    """

    def __getitem__(self, key: Any) -> Any:
        return self.get(key)

    def get(self, key: Any, default: Any = None) -> Any:  # type: ignore[override]
        return super().get(key, default)


@dataclass
class AppConfig:
    """
    Central configuration object.

    The class stores configuration data in a ``TolerantDict`` and provides a
    ``get`` method for dictionary‑style access.  It also implements ``__getattr__``
    to return a no‑op callable for any undefined attribute, allowing the object
    to be used as a lightweight logger throughout the codebase.
    """

    config: TolerantDict = field(default_factory=TolerantDict)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value using dot‑notation or nested dictionaries.

        Example:
            config.get("paths.base", "projects/PROJ-179-the-influence-of-metacognitive-awareness")
        """
        parts = key.split(".")
        current: Any = self.config
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, default)
            else:
                return default
        return current if current is not None else default

    def __getattr__(self, name: str):
        """
        Return a no‑op function for any attribute that does not exist.
        This makes ``config.info(...)``, ``config.debug(...)`` etc. safe.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

    def update(self, other: Dict[str, Any]) -> None:
        """
        Merge another mapping into the internal configuration.
        """
        if not isinstance(other, dict):
            raise ValueError("AppConfig.update expects a dictionary")
        self.config.update(other)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load a JSON configuration file into an ``AppConfig`` instance.

    If ``config_path`` is ``None`` the function looks for a ``config.json`` file
    in the project root.  Missing files result in an empty configuration rather
    than an exception – this keeps the pipeline robust in environments where a
    configuration file is optional.
    """
    if config_path is None:
        # Assume the project root is two levels up from this file (code/config/)
        config_path = Path(__file__).resolve().parents[2] / "config.json"

    cfg = AppConfig()
    if config_path.is_file():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg.update(data)
        except json.JSONDecodeError as exc:
            logging.warning(f"Failed to parse config file {config_path}: {exc}")
    else:
        logging.info(f"No configuration file found at {config_path}; using defaults.")
    return cfg


def setup_logging(level: str = "INFO") -> None:
    """
    Configure the root logger with a simple format.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def get_seed(env_var: str = "PROJECT_SEED", default: int = 42) -> int:
    """
    Retrieve a random seed from the environment or fall back to a default.
    """
    try:
        return int(os.getenv(env_var, default))
    except ValueError:
        logging.warning(
            f"Environment variable {env_var} is not a valid integer; using default {default}"
        )
        return default


def main() -> None:
    """
    Entry‑point used by the CLI ``python -m code.config.env_config``.
    It simply loads the configuration and prints it – useful for debugging.
    """
    cfg = load_config()
    print(json.dumps(cfg.config, indent=2))