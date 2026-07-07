"""
Configuration Management Module (T006)

Handles path resolution, directory creation, and configuration loading.
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Project root is the directory containing 'code', 'data', etc.
# We assume the script is run from the project root.
PROJECT_ROOT = Path(__file__).parent.parent

CONFIG_FILE = PROJECT_ROOT / "config.yaml"
ENV_FILE = PROJECT_ROOT / ".env"

def get_config_dict() -> Dict[str, Any]:
    """Load configuration from config.yaml or return defaults."""
    config = {
        "data": {
            "raw": str(PROJECT_ROOT / "data" / "raw"),
            "processed": str(PROJECT_ROOT / "data" / "processed"),
            "models": str(PROJECT_ROOT / "data" / "models"),
            "figures": str(PROJECT_ROOT / "data" / "figures"),
            # Default URLs for testing if config.yaml is missing
            "yearly_cps_urls": [] 
        },
        "paths": {
            "root": str(PROJECT_ROOT)
        }
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded = yaml.safe_load(f)
                # Deep merge not implemented for simplicity, just update top level
                if loaded:
                    for key in loaded:
                        if isinstance(loaded[key], dict) and key in config and isinstance(config[key], dict):
                            config[key].update(loaded[key])
                        else:
                            config[key] = loaded[key]
        except Exception as e:
            print(f"Warning: Failed to load config.yaml: {e}. Using defaults.")
    elif ENV_FILE.exists():
        # Simple env file parsing if yaml not present
        # Not implemented for full .env support, assuming yaml is primary
        pass

    return config

def get_path(*parts: str) -> Path:
    """
    Resolve a path relative to the project root or a specific data directory.
    Usage: get_path('data', 'raw') -> PROJECT_ROOT/data/raw
    """
    # If the first part is a known data directory, resolve relative to project root
    base = PROJECT_ROOT
    if parts and parts[0] in ['data', 'code', 'tests', 'specs', 'contracts']:
        base = PROJECT_ROOT / parts[0]
        parts = parts[1:]
    
    return base / os.path.join(*parts)

def ensure_directories():
    """Create all necessary directories defined in config."""
    config = get_config_dict()
    dirs = [
        config['data']['raw'],
        config['data']['processed'],
        config['data']['models'],
        config['data']['figures']
    ]
    for d in dirs:
        path = Path(d)
        path.mkdir(parents=True, exist_ok=True)
