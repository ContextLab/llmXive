"""
Configuration management for seeds, paths, and hyperparameters.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List

class Config:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config.yaml")
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                # Simple YAML/JSON loader placeholder
                # In real implementation, use pyyaml or json
                return json.load(f) if self.config_path.suffix == ".json" else {}
        return {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

def get_config(config_path: Optional[Path] = None) -> Config:
    return Config(config_path)

def get_path(key: str, base: Optional[Path] = None) -> Path:
    config = get_config()
    val = config.get(key)
    if val is None:
        raise KeyError(f"Path key {key} not found in config")
    return base / val if base else Path(val)

def get_hyperparameter(key: str) -> Any:
    config = get_config()
    return config.get(key)

def get_seed() -> int:
    config = get_config()
    return config.get("seed", 42)
