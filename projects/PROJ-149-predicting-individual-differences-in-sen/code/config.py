"""
code/config.py

Central configuration for the project.
Defines paths, filter parameters, seeds, and band definitions.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default configuration
_CONFIG = {
    'seed': 42,
    'paths': {
        'data_raw': 'data/raw',
        'data_interim': 'data/interim',
        'data_processed': 'data/processed',
        'figures': 'figures',
        'code': 'code',
    },
    'filter_params': {
        'lowcut': 1.0,
        'highcut': 45.0,
        'notch_freqs': [50, 60],
    },
    'band_freqs': {
        'delta': (1, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'low_beta': (13, 20),
        'high_beta': (20, 30),
        'gamma': (30, 45),
    },
    'overlap_seconds': 2.0,
    'window_seconds': 4.0,
}

# Global seed state
_GLOBAL_SEED = None

def set_global_seed(seed: int):
    """Set global seed for reproducibility."""
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> Optional[int]:
    """Get the current global seed."""
    return _GLOBAL_SEED if _GLOBAL_SEED is not None else _CONFIG.get('seed')

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file if exists, otherwise use defaults."""
    if config_path is None:
        config_path = PROJECT_ROOT / 'config.yaml'
    
    config_path = Path(config_path)
    if config_path.exists():
        with open(config_path, 'r') as f:
            custom_config = yaml.safe_load(f)
            # Deep merge with defaults
            _CONFIG = _deep_merge(_CONFIG, custom_config)
    return _CONFIG

def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def get_path(relative_path: str) -> Path:
    """Get absolute path for a relative path defined in config."""
    # Normalize path separators
    relative_path = relative_path.replace('/', os.sep)
    
    # Check if it's a full path already
    if relative_path.startswith('/'):
        return Path(relative_path)
    
    # Check in paths config
    paths_config = _CONFIG.get('paths', {})
    for key, path in paths_config.items():
        if relative_path.startswith(key):
            base = PROJECT_ROOT / path
            remainder = relative_path[len(key):].lstrip(os.sep)
            return base / remainder if remainder else base
    
    # Default to data_processed or code if not found
    return PROJECT_ROOT / 'data' / 'processed' / relative_path

def ensure_dirs(file_path: str | Path):
    """Ensure the directory for a file path exists."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

def get_filter_params() -> Dict[str, Any]:
    """Get filter parameters."""
    return _CONFIG.get('filter_params', {})

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Get frequency band definitions."""
    return _CONFIG.get('band_freqs', {})

def get_all_band_names() -> List[str]:
    """Get list of all band names."""
    return list(get_band_freqs().keys())

def get_overlap_seconds() -> float:
    """Get overlap duration in seconds."""
    return _CONFIG.get('overlap_seconds', 2.0)

def get_window_seconds() -> float:
    """Get window duration in seconds."""
    return _CONFIG.get('window_seconds', 4.0)

# Initialize config on import
_CONFIG = load_config()
set_global_seed(_CONFIG.get('seed', 42))
