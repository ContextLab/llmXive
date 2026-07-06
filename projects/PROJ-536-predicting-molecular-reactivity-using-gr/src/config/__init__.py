"""
Configuration management module for PROJ-536.
Loads and validates defaults from YAML.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict

# Resolve project root relative to this file's location
_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _ROOT / "src" / "config" / "defaults.yaml"

_config_data: Dict[str, Any] = {}

def load_config() -> Dict[str, Any]:
    """Load configuration from defaults.yaml."""
    global _config_data
    if not _config_data:
        if not _CONFIG_PATH.exists():
            raise FileNotFoundError(f"Configuration file not found at {_CONFIG_PATH}")
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_data = yaml.safe_load(f)
    return _config_data

def get_config(key: str = None, default: Any = None) -> Any:
    """
    Retrieve a configuration value.
    Supports dot-notation for nested keys (e.g., 'model.learning_rate').
    """
    cfg = load_config()
    if key is None:
        return cfg

    parts = key.split(".")
    val = cfg
    try:
        for part in parts:
            val = val[part]
        return val
    except (KeyError, TypeError):
        return default

def get_paths() -> Dict[str, str]:
    """Return absolute paths for all configured directories."""
    cfg = load_config()
    base_paths = cfg.get("paths", {})
    absolute_paths = {}
    for name, rel_path in base_paths.items():
        absolute_paths[name] = str(_ROOT / rel_path)
    return absolute_paths
