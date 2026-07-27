"""
Configuration management for the project.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

def load_config(config_path: str = "data/config/project_config.yaml") -> Config:
    """Loads project configuration."""
    path = Path(config_path)
    if path.exists():
        import yaml
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return Config(data)
    else:
        # Default config
        return Config({
            "required_variables": {
                "predictors": [f"Taxon_{i}" for i in range(1, 21)],
                "outcomes": ["SWS_duration", "REM_duration", "Sleep_Efficiency", "Wake_after_sleep_onset"]
            }
        })

def get_config() -> Config:
    """Returns the global config instance."""
    return load_config()

def main():
    pass
