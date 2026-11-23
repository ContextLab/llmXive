import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

class Config:
    """
    Configuration handler for the project.
    Supports dictionary-style access for compatibility with callers expecting subscriptable config.
    """
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}
        # Set defaults
        self._config.setdefault("paths", {})
        self._config["paths"].setdefault("output_dir", "data/derived")
        self._config["paths"].setdefault("figures_dir", "figures")
        self._config["paths"].setdefault("raw_dir", "data/raw")
        self._config.setdefault("api", {})
        self._config["api"].setdefault("github_token", os.getenv("GITHUB_TOKEN", ""))

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value by dot-separated key path."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def __getitem__(self, key: str) -> Any:
        """Enable dictionary-style access (e.g., config['paths']['output_dir'])."""
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        return key in self._config

    def keys(self):
        return self._config.keys()

    def values(self):
        return self._config.values()

    def items(self):
        return self._config.items()

    def __repr__(self):
        return f"Config({self._config})"

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a JSON file or return defaults.
    
    Args:
        config_path: Path to config.json. If None, uses default paths.
    
    Returns:
        Config object.
    """
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            data = json.load(f)
        return Config(data)
    return Config()
