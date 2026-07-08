import os
import yaml
from typing import Optional, Dict, Any

__all__ = ["Config", "get_config"]

class Config:
    """
    Simple configuration container.

    Attributes are loaded from a YAML file whose path is provided via the
    ``PROJ_CONFIG`` environment variable or defaults to ``config.yaml`` in
    the project root.
    """

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getattr__(self, item):
        return self._data.get(item)

    def __repr__(self):
        return f"Config({self._data})"

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a YAML file.

    Parameters
    ----------
    config_path: str, optional
        Explicit path to the configuration file.  If omitted, the function
        checks the ``PROJ_CONFIG`` environment variable and falls back to
        ``config.yaml`` in the current working directory.

    Returns
    -------
    Config
        Configuration object.
    """
    if config_path is None:
        config_path = os.getenv("PROJ_CONFIG", "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r") as f:
        data = yaml.safe_load(f) or {}
    return Config(data)
