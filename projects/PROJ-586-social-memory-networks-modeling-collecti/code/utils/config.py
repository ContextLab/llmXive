"""
utils.config
---------------
Configuration utilities for the project.

Provides:
- load_config(): Load configuration from ``config.yaml`` located in the same
  directory as this module. Returns a dictionary with default values if the
  file does not exist.
- save_config(config): Persist a configuration dictionary to ``config.yaml``.

The module is deliberately lightweight and has no external runtime
dependencies beyond ``pyyaml`` (added to ``requirements.txt``).
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict

__all__ = ["load_config", "save_config"]

# Path to the yaml configuration file that lives next to this module.
_CONFIG_PATH = Path(__file__).with_name("config.yaml")

# Default configuration used when no file is present.
_DEFAULT_CONFIG: Dict[str, Any] = {
    "seed": 42,
    "device": "cpu",
}


def load_config() -> Dict[str, Any]:
    """
    Load the project configuration from ``config.yaml``.

    Returns
    -------
    dict
        Configuration dictionary. If the file does not exist or is malformed,
        the default configuration is returned.
    """
    if not _CONFIG_PATH.is_file():
        # No config file – return defaults.
        return dict(_DEFAULT_CONFIG)

    try:
        with _CONFIG_PATH.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        # Any error (e.g., parsing) falls back to defaults.
        return dict(_DEFAULT_CONFIG)

    # Merge defaults with loaded values (loaded overrides defaults).
    merged = dict(_DEFAULT_CONFIG)
    merged.update(cfg)
    return merged


def save_config(config: Dict[str, Any]) -> None:
    """
    Persist ``config`` to ``config.yaml``.

    Parameters
    ----------
    config : dict
        Configuration dictionary to write. Keys that are not serialisable by
        ``yaml.safe_dump`` will raise a ``yaml.YAMLError``.
    """
    # Ensure the parent directory exists (it will, but guard for safety).
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _CONFIG_PATH.open("w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False)