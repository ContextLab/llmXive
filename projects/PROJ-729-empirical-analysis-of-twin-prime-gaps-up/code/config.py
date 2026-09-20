"""
Configuration Loader Module.

Provides centralized access to project configuration, paths, and limits.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

def get_config() -> Dict[str, Any]:
    """
    Load configuration from a config.json file or return defaults.
    
    Returns a dictionary with:
      - paths: { 'raw', 'results', 'figures', 'contracts' }
      - limits: { 'max_prime' }
      - schema_path: path to schema file
      - state_path: path to state file
    """
    # Default configuration
    config = {
        "paths": {
            "raw": "data/raw",
            "results": "data/results",
            "figures": "data/figures",
            "contracts": "contracts"
        },
        "limits": {
            "max_prime": 10**9
        },
        "schema_path": "contracts/twin_prime_schema.schema.yaml",
        "state_path": "data/state.yaml"
    }
    
    # Try to load from a config file if it exists
    config_file = Path("config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                loaded = json.load(f)
                # Merge loaded config with defaults
                for key, value in loaded.items():
                    if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                        config[key].update(value)
                    else:
                        config[key] = value
        except Exception as e:
            # Log warning but continue with defaults
            print(f"Warning: Could not load config.json: {e}")
    
    return config

def ensure_directories(paths: list) -> None:
    """
    Ensure that the given list of paths exist as directories.
    Creates them if they don't.
    """
    for path in paths:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)

def get_schema_path() -> str:
    """
    Return the path to the schema file.
    """
    return get_config()['schema_path']

def get_state_path() -> str:
    """
    Return the path to the state file.
    """
    return get_config()['state_path']
