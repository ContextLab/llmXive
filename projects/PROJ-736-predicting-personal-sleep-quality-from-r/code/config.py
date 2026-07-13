"""
Configuration utilities for the sleep quality prediction project.
Provides path management, simple configuration handling, and directory creation.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Union

# Base directory of the project (one level up from this file's directory)
BASE_DIR = Path(__file__).resolve().parent.parent


def get_paths() -> Dict[str, str]:
    """
    Return a dictionary of important filesystem paths used throughout the project.

    Keys:
        raw:        Directory for raw downloaded data.
        processed: Directory for processed data (features, predictions, etc.).
        logs:       Directory for JSON log files.
        figures:    Directory for generated figures.
        results:    Directory for final result artifacts (e.g., ResultReport.json).
    """
    return {
        "raw": str(BASE_DIR / "data" / "raw"),
        "processed": str(BASE_DIR / "data" / "processed"),
        "logs": str(BASE_DIR / "data" / "logs"),
        "figures": str(BASE_DIR / "data" / "figures"),
        "results": str(BASE_DIR / "data" / "results"),
    }


def get_config() -> Dict[str, Any]:
    """
    Load a simple JSON configuration file if it exists.
    The configuration file is optional; an empty dict is returned if absent.
    """
    config_path = BASE_DIR / "config.json"
    if config_path.is_file():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def set_config(new_config: Dict[str, Any]) -> None:
    """
    Persist a configuration dictionary to ``config.json`` in the project root.
    Overwrites any existing configuration.
    """
    config_path = BASE_DIR / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(new_config, f, indent=2)


def ensure_dirs(paths: Union[Dict[str, str], list, tuple, set, str]) -> None:
    """
    Ensure that all directory paths provided exist.

    The function is flexible and accepts:
        * a dict of paths (values are strings)
        * an iterable of path strings (list, tuple, set)
        * a single path string

    Non‑existent directories are created (including parent directories).
    """
    if isinstance(paths, dict):
        iterable = paths.values()
    elif isinstance(paths, (list, tuple, set)):
        iterable = paths
    else:  # Assume a single path string
        iterable = [paths]

    for path in iterable:
        if not path:
            continue
        Path(path).mkdir(parents=True, exist_ok=True)
