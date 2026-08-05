"""
Environment management and reproducibility utilities.

This module handles:
- Loading configuration
- Setting up random seeds
- Managing project paths
"""
import os
import sys
import random
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError:
            return {}

def deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def setup_reproducibility(seed: int = 42) -> None:
    """
    Setup reproducibility by setting random seeds.
    
    Args:
        seed: Random seed value.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # If numpy is available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    logging.info(f"Reproducibility setup with seed: {seed}")

def get_paths() -> Dict[str, Path]:
    """
    Get standard project paths.
    
    Returns:
        Dictionary of path names to Path objects.
    """
    root = get_project_root()
    
    return {
        'root': root,
        'data_raw': root / 'data' / 'raw',
        'data_derived': root / 'data' / 'derived',
        'data_processed': root / 'data' / 'processed',
        'state': root / 'state',
        'logs': root / 'logs',
        'output': root / 'output',
        'config': root / 'code' / 'config.yaml',
        'raw_eye_tracking': root / 'data' / 'raw' / 'eye_tracking_raw.parquet',
        'preprocessed_gaze': root / 'data' / 'derived' / 'preprocessed_gaze.csv',
        'empirical_outcomes': root / 'data' / 'derived' / 'empirical_outcomes.csv',
    }

def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Get a value from configuration with a default fallback.
    
    Args:
        config: Configuration dictionary.
        key: Key to look up.
        default: Default value if key not found.
        
    Returns:
        Configuration value or default.
    """
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def setup_logging(log_dir: Optional[Path] = None) -> None:
    """Setup basic logging."""
    import logging
    from logging_config import setup_logging as setup_log
    setup_log(log_dir)

def main():
    """Test environment manager."""
    paths = get_paths()
    print(f"Project root: {paths['root']}")
    print(f"Data raw: {paths['data_raw']}")

if __name__ == "__main__":
    main()
