import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

_CONFIG: Optional[Dict[str, Any]] = None
_CONFIG_PATH: Optional[Path] = None

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Loads the configuration from a YAML file.
    Defaults to 'config.yaml' in the project root if no path is provided.
    """
    global _CONFIG, _CONFIG_PATH
    
    if config_path is None:
        # Try common locations
        possible_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("data/config.yaml"),
            Path("specs/config.yaml"),
        ]
        for p in possible_paths:
            if p.exists():
                config_path = p
                break
        if config_path is None:
            # Create a minimal default config if none found
            _CONFIG = {
                "paths": {
                    "raw_data": "data/raw",
                    "processed_data": "data/processed",
                    "results": "data/results",
                    "ingested_data_path": "data/processed/labels.parquet",
                    "existing_features_path": "data/processed/features_partial.parquet",
                    "output_features_path": "data/processed/features.parquet"
                },
                "seeds": {
                    "random": 42
                },
                "hyperparameters": {}
            }
            _CONFIG_PATH = None
            return _CONFIG
    
    _CONFIG_PATH = Path(config_path)
    with open(_CONFIG_PATH, 'r') as f:
        _CONFIG = yaml.safe_load(f)
    
    return _CONFIG

def get_config() -> Dict[str, Any]:
    """Returns the loaded configuration."""
    if _CONFIG is None:
        return load_config()
    return _CONFIG

def get_path(config: Dict[str, Any], key: str, default: Optional[str] = None) -> str:
    """
    Retrieves a path from the config dictionary.
    Supports nested keys like 'paths.raw_data'.
    """
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            if default is not None:
                return default
            raise KeyError(f"Config key '{key}' not found")
    return str(value)

def get_seed(key: str = "random") -> int:
    """Retrieves a seed value from the config."""
    config = get_config()
    try:
        return int(get_path(config, f"seeds.{key}", 42))
    except (KeyError, ValueError):
        return 42

def get_hyperparameter(key: str, default: Any = None) -> Any:
    """Retrieves a hyperparameter from the config."""
    config = get_config()
    try:
        return get_path(config, f"hyperparameters.{key}", default)
    except KeyError:
        return default

def get_simulation_config() -> Dict[str, Any]:
    """Retrieves the simulation configuration block."""
    config = get_config()
    return get_path(config, "simulation", {})

def save_config(config: Dict[str, Any], path: Optional[Union[str, Path]] = None) -> None:
    """Saves the configuration to a YAML file."""
    if path is None:
        path = "config.yaml"
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)