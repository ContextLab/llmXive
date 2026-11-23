"""
r_config.py
-------------
Helper module for loading environment configuration related to R script locations
and memory limits. This centralizes configuration management so that other parts
of the pipeline can retrieve these settings without hard‑coding values.

The configuration is stored in ``code/config.yaml``. If the file is missing or
malformed, a clear exception is raised to surface the problem during execution.
"""

import os
from pathlib import Path
from typing import Any, Dict

try:
    import yaml
except ImportError as exc:
    raise ImportError(
        "PyYAML is required for configuration loading. Install it via "
        "`pip install pyyaml`."
    ) from exc


# Path to the YAML configuration file located at the project root
_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"

_CONFIG_CACHE: Dict[str, Any] = {}


def _load_config() -> Dict[str, Any]:
    """
    Load the YAML configuration file.

    Returns
    -------
    dict
        Parsed configuration dictionary.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist.
    yaml.YAMLError
        If the file cannot be parsed as valid YAML.
    """
    if not _CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found at {_CONFIG_PATH}")

    with _CONFIG_PATH.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    if not isinstance(config, dict):
        raise yaml.YAMLError("Configuration file must contain a mapping at the top level.")

    return config


def _get_config() -> Dict[str, Any]:
    """
    Retrieve the configuration, using a cached version if already loaded.
    """
    global _CONFIG_CACHE
    if not _CONFIG_CACHE:
        _CONFIG_CACHE = _load_config()
    return _CONFIG_CACHE


def get_r_script_dir() -> Path:
    """
    Return the directory that contains R scripts.

    Returns
    -------
    pathlib.Path
        Path object pointing to the R script directory.

    Raises
    ------
    KeyError
        If ``R_SCRIPT_DIR`` is not defined in the configuration.
    """
    cfg = _get_config()
    dir_str = cfg["R_SCRIPT_DIR"]
    return Path(dir_str).resolve()


def get_r_script_path() -> Path:
    """
    Return the full path to the main R differential expression script.

    Returns
    -------
    pathlib.Path
        Path object pointing to the R script.

    Raises
    ------
    KeyError
        If ``R_SCRIPT_PATH`` is not defined in the configuration.
    """
    cfg = _get_config()
    path_str = cfg["R_SCRIPT_PATH"]
    return Path(path_str).resolve()


def get_memory_limit_mb() -> int:
    """
    Retrieve the hard memory limit (in megabytes) for the pipeline.

    Returns
    -------
    int
        Memory limit in MB.

    Raises
    ------
    KeyError
        If ``MEMORY_LIMIT_MB`` is not defined in the configuration.
    """
    cfg = _get_config()
    return int(cfg["MEMORY_LIMIT_MB"])


def get_memory_warning_threshold_mb() -> int:
    """
    Retrieve the memory warning threshold (in megabytes). When usage exceeds this
    value, the pipeline should emit a warning but may continue.

    Returns
    -------
    int
        Memory warning threshold in MB.

    Raises
    ------
    KeyError
        If ``MEMORY_WARNING_THRESHOLD_MB`` is not defined in the configuration.
    """
    cfg = _get_config()
    return int(cfg["MEMORY_WARNING_THRESHOLD_MB"])


# Backward compatibility helpers (mirroring the original config module API)
# These simply delegate to the new functions so existing imports continue to work.

def ensure_directories() -> None:
    """
    Ensure that required output directories exist. This function mirrors the
    original ``ensure_directories`` from ``src.config`` but also guarantees that
    the R script directory exists (creating it if necessary). It is safe to call
    multiple times.
    """
    from src.config import ensure_directories as _ensure_src_dirs

    # Ensure the generic project directories first
    _ensure_src_dirs()

    # Then ensure the R script directory exists
    r_dir = get_r_script_dir()
    r_dir.mkdir(parents=True, exist_ok=True)


# Export symbols for ``from src.r_config import *``
__all__ = [
    "get_r_script_dir",
    "get_r_script_path",
    "get_memory_limit_mb",
    "get_memory_warning_threshold_mb",
    "ensure_directories",
]