import yaml
import os
from pathlib import Path

def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_paths(config: dict) -> dict:
    """Extract path configurations from the loaded config."""
    return config.get('paths', {})
