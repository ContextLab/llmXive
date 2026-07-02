from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

# Default configuration file path (relative to the project root)
DEFAULT_CONFIG_PATH = Path("code/utils/config.yaml")


def load_config(path: Path | None = None) -> Dict[str, Any]:
    """
    Load a configuration file (YAML preferred, fallback to JSON) and return it as a dict.

    If the file does not exist, an empty dict is returned.

    Parameters
    ----------
    path: Path | None
        Optional custom path to the config file. If None, DEFAULT_CONFIG_PATH is used.

    Returns
    -------
    dict
        Configuration dictionary.
    """
    cfg_path = path or DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        return {}
    try:
        import yaml  # type: ignore
        with cfg_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data
    except Exception:
        # If YAML parsing fails (or yaml not installed), fall back to JSON.
        with cfg_path.open("r", encoding="utf-8") as f:
            return json.load(f)


def save_config(config: Dict[str, Any], path: Path | None = None) -> None:
    """
    Save a configuration dictionary to a file (YAML preferred, fallback to JSON).

    Parameters
    ----------
    config: dict
        Configuration data to write.
    path: Path | None
        Optional custom path to the config file. If None, DEFAULT_CONFIG_PATH is used.
    """
    cfg_path = path or DEFAULT_CONFIG_PATH
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml  # type: ignore
        with cfg_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(config, f)
    except Exception:
        # Fallback to JSON if yaml is unavailable or fails.
        with cfg_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
