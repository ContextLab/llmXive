"""Configuration management for the project."""
import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional, Union
import yaml

from .exceptions import DataInsufficientError

CONFIG_PATH = Path(__file__).parent / "config.yaml"

class Config:
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        if key not in self._config:
            raise KeyError(f"Configuration key '{key}' not found")
        return self._config[key]

_global_config: Optional[Config] = None

def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from YAML file."""
    non_local_path = config_path or CONFIG_PATH
    if not non_local_path.exists():
        raise FileNotFoundError(f"Config file not found: {non_local_path}")
    
    with open(non_local_path, 'r') as f:
        data = yaml.safe_load(f)
    
    return Config(data)

def set_global_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = _global_config.get('random_seed', 42) if _global_config else 42
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config() -> Config:
    """Get the global configuration instance."""
    if _global_config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")
    return _global_config

def get_path(key: str) -> Path:
    """Get a path from configuration and resolve it relative to project root."""
    val = get_config()[key]
    base = Path(__file__).parent.parent
    return (base / val).resolve()
