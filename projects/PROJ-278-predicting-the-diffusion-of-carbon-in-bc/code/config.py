"""Configuration management for the diffusion prediction pipeline."""
import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Global config instance
_config: Optional[Dict[str, Any]] = None

class Config:
    """Configuration object wrapper for type safety and path resolution."""
    def __init__(self, config_dict: Dict[str, Any]):
        self._data = config_dict
        self.random_seed = config_dict.get('random_seed', 42)
        self.data_path = config_dict.get('data_path', 'data/raw')
        self.output_path = config_dict.get('output_path', 'data/outputs')
        self.processed_path = config_dict.get('processed_path', 'data/processed')
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    global _config
    if _config is None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        import yaml
        with open(path, 'r') as f:
            _config = yaml.safe_load(f)
    return _config

def set_global_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        cfg = load_config()
        seed = cfg.get('random_seed', 42)
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config() -> Dict[str, Any]:
    """Get the loaded configuration dictionary."""
    return load_config()

def get_path(*args, **kwargs) -> Path:
    """
    Flexible path resolution helper to support multiple calling conventions.
    
    Conventions supported:
    1. get_path("relative/path") -> Path("relative/path")
    2. get_path("base_key", "sub_key") -> Path(config[base_key]) / sub_key
    3. get_path(config_dict, "base_key", "sub_key") -> Path(config_dict[base_key]) / sub_key
    4. get_path(config_obj, "base_key", "sub_key") -> Path(config_obj[base_key]) / sub_key
    5. get_path("base_key", "sub_key", create=True) -> Creates directories if needed
    6. get_path("logs") -> Returns Path for logs directory (special case for setup_logging.py)
    """
    # Handle keyword argument 'create'
    create_dirs = kwargs.get('create', False)
    
    # Case 1: Single string argument (direct path)
    if len(args) == 1 and isinstance(args[0], str):
        p = Path(args[0])
        if create_dirs:
            p.mkdir(parents=True, exist_ok=True)
        return p
    
    # Case 2: First arg is a dict or Config object
    if len(args) >= 2:
        first_arg = args[0]
        
        # Extract config dict
        if isinstance(first_arg, dict):
            cfg = first_arg
        elif isinstance(first_arg, Config):
            cfg = first_arg._data
        else:
            # Try to load global config if first arg is not a dict/object
            cfg = load_config()
        
        base_key = args[1]
        base_path = cfg.get(base_key, base_key)
        
        # If base_path is already a Path, convert to string for joining
        if isinstance(base_path, Path):
            base_path = str(base_path)
        
        # Build the final path
        if len(args) > 2:
            # Additional path components
            final_path = Path(base_path) / os.path.join(*args[2:])
        else:
            final_path = Path(base_path)
        
        if create_dirs:
            final_path.mkdir(parents=True, exist_ok=True)
        
        return final_path
    
    # Fallback: treat all args as path components
    p = Path(*args)
    if create_dirs:
        p.mkdir(parents=True, exist_ok=True)
    return p

# Backward compatibility aliases for specific call patterns found in codebase
def get_config_path(key: str) -> Path:
    """Legacy helper for specific config key access."""
    cfg = load_config()
    val = cfg.get(key)
    if val is None:
        raise KeyError(f"Config key '{key}' not found")
    return Path(val)