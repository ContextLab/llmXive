"""
Configuration management utilities.

The pipeline uses a simple YAML configuration file.  The default location
is ``code/utils/config.yaml``.  Call ``load_config()`` to obtain a dictionary
with the configuration values.  ``get_config()`` caches the result so that
the file is read only once per interpreter session.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

_CACHED_CONFIG: Optional[Dict[str, Any]] = None

# Resolve the default configuration file location relative to this file
_DEFAULT_CONFIG_PATH = Path(__file__).with_name("config.yaml")

def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a YAML configuration file.

    Parameters
    ----------
    path : pathlib.Path, optional
        Path to a YAML configuration file.  If ``None`` the default
        ``code/utils/config.yaml`` is used.  The environment variable
        ``PROJ_CONFIG`` can also be used to point to an alternative file.

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
    # Environment variable takes precedence over the argument
    env_path = os.getenv("PROJ_CONFIG")
    if env_path:
        config_path = Path(env_path).expanduser().resolve()
    else:
        config_path = path or _DEFAULT_CONFIG_PATH

    if not config_path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with config_path.open("rt", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    return cfg

def get_config() -> Dict[str, Any]:
    """
    Return the cached configuration dictionary.

    The configuration file is read only once; subsequent calls return the
    same dictionary object.  This is safe because the dictionary contents
    are not mutated by the library.

    Returns
    -------
    dict
        The configuration dictionary.
    """
    global _CACHED_CONFIG
    if _CACHED_CONFIG is None:
        _CACHED_CONFIG = load_config()
    return _CACHED_CONFIG
