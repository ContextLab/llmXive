"""Configuration management."""
import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional, Union

class Config:
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML or JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    path = Path(config_path)
    if not path.exists():
        # Default config
        return Config({
            "random_seed": 42,
            "data_path": "data/raw",
            "output_path": "data/outputs"
        })
    
    with open(path, 'r') as f:
        if path.suffix == '.yaml' or path.suffix == '.yml':
            import yaml
            config_dict = yaml.safe_load(f)
        else:
            config_dict = json.load(f)
    
    return Config(config_dict)

def set_global_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def get_config() -> Config:
    """Get the global configuration."""
    return load_config()

def get_path(key: str) -> Path:
    """Get a path from configuration."""
    config = get_config()
    path_str = config.get(key, "")
    return Path(path_str)
