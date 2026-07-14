"""
Configuration management for the project.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default configuration
DEFAULT_CONFIG = {
    'random_seed': 42,
    'max_memory_gb': 7.0,
    'max_runtime_seconds': 3600 * 6, # 6 hours
    'dataset_id': 'ds000246',
    'data_dir': PROJECT_ROOT / 'data',
    'code_dir': PROJECT_ROOT / 'code',
    'output_dir': PROJECT_ROOT / 'data' / 'processed',
    'figures_dir': PROJECT_ROOT / 'data' / 'figures',
}

def get_config(key: Optional[str] = None) -> Any:
    """
    Get a configuration value.
    If key is None, return the full config dict.
    """
    config = DEFAULT_CONFIG.copy()
    # Allow environment variable overrides
    for k, v in config.items():
        env_key = f"XIVE_{k.upper()}"
        if env_key in os.environ:
            val = os.environ[env_key]
            # Try to convert to int/float if possible
            try:
                if '.' in val:
                    config[k] = float(val)
                else:
                    config[k] = int(val)
            except ValueError:
                config[k] = val
    
    if key:
        return config.get(key)
    return config

def ensure_dir(directory: Path) -> None:
    """Ensure a directory exists."""
    directory.mkdir(parents=True, exist_ok=True)
