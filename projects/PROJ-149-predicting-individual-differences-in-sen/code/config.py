"""
Configuration management and random seed pinning for the EEG Sensory Speed project.

This module handles:
- Global random seed pinning for reproducibility (Python, NumPy, random modules).
- Loading configuration from YAML files.
- Path management for project directories.
- Retrieval of filter parameters and frequency band definitions.
"""
import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"

# Global Seed State
_GLOBAL_SEED = 42

def set_global_seed(seed: int) -> None:
    """
    Set the random seed for Python's random, NumPy, and any other relevant libraries
    to ensure reproducibility across runs.

    Args:
        seed (int): The integer seed value to use.
    """
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Note: MNE and other libraries often rely on numpy's seed.
    # If specific libraries like PyTorch were used, their seeds would be set here too.
    # os.environ['PYTHONHASHSEED'] = str(seed) # Optional: for hash randomization control

def get_seed() -> int:
    """
    Retrieve the currently set global seed.

    Returns:
        int: The global seed value.
    """
    return _GLOBAL_SEED

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path (Path, optional): Path to the config file. Defaults to CONFIG_PATH.

    Returns:
        Dict[str, Any]: Configuration dictionary.
    
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    if config_path is None:
        config_path = CONFIG_PATH
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def ensure_dirs() -> None:
    """
    Create necessary project directories if they do not exist.
    Uses paths defined in the config or defaults.
    """
    config = load_config()
    base_dirs = [
        'data/raw',
        'data/interim',
        'data/processed',
        'figures',
        'code/utils',
        'tests'
    ]
    
    # Check if base paths are overridden in config, otherwise use defaults
    for dir_name in base_dirs:
        dir_path = PROJECT_ROOT / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

def get_path(key: str, config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Resolve a path from the configuration or default structure.

    Args:
        key (str): The key in the config (e.g., 'paths.raw_data').
        config (Dict, optional): Config dict. If None, loads default.

    Returns:
        Path: Resolved absolute path.
    """
    if config is None:
        config = load_config()
    
    # Navigate nested keys
    keys = key.split('.')
    val = config
    try:
        for k in keys:
            val = val[k]
    except KeyError:
        # Fallback to default project structure if key not found in config
        # This ensures robustness if config is minimal
        if key == 'paths.raw_data':
            return PROJECT_ROOT / 'data' / 'raw'
        elif key == 'paths.interim_data':
            return PROJECT_ROOT / 'data' / 'interim'
        elif key == 'paths.processed_data':
            return PROJECT_ROOT / 'data' / 'processed'
        elif key == 'paths.figures':
            return PROJECT_ROOT / 'figures'
        else:
            raise KeyError(f"Path key '{key}' not found in config and no default defined.")
    
    # If the value is a relative path string, resolve it against PROJECT_ROOT
    if isinstance(val, str):
        return PROJECT_ROOT / val
    return Path(val)

def get_filter_params(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Retrieve EEG filtering parameters (bandpass, notch, etc.).

    Args:
        config (Dict, optional): Config dict.

    Returns:
        Dict[str, Any]: Dictionary of filter parameters.
    """
    if config is None:
        config = load_config()
    
    # Default fallbacks if config is missing specific sections
    defaults = {
        'bandpass_low': 1.0,
        'bandpass_high': 40.0,
        'notch_freq': 50.0, # Default to 50Hz, can be 60
        'variance_threshold_sd': 3.0,
        'ica_components': 20
    }
    
    filter_cfg = config.get('filter_params', {})
    return {**defaults, **filter_cfg}

def get_band_freqs(config: Optional[Dict[str, Any]] = None) -> Dict[str, Tuple[float, float]]:
    """
    Retrieve frequency band definitions.

    Returns:
        Dict[str, Tuple[float, float]]: Mapping of band name to (low, high) frequency.
    """
    if config is None:
        config = load_config()
    
    # Default definitions aligned with task description
    defaults = {
        'delta': (1.0, 4.0),
        'theta': (4.0, 8.0),
        'alpha': (8.0, 13.0),
        'low_beta': (13.0, 20.0),
        'high_beta': (20.0, 30.0),
        'gamma': (30.0, 40.0)
    }
    
    bands_cfg = config.get('band_freqs', {})
    # Merge defaults with config, ensuring types are correct
    result = {}
    for name, (low, high) in defaults.items():
        if name in bands_cfg:
            cfg_val = bands_cfg[name]
            if isinstance(cfg_val, list) and len(cfg_val) == 2:
                result[name] = (float(cfg_val[0]), float(cfg_val[1]))
            else:
                result[name] = (low, high)
        else:
            result[name] = (low, high)
    
    return result

def get_all_band_names(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Get a list of all defined band names in order.

    Returns:
        List[str]: List of band names.
    """
    return list(get_band_freqs(config).keys())

# Initialize seed on module load to ensure immediate reproducibility
# This can be overridden by calling set_global_seed() later in the pipeline.
set_global_seed(_GLOBAL_SEED)
