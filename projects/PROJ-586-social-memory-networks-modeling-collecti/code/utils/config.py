"""Environment management and configuration."""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_CONFIG = {
    "seed": 42,
    "device": "cpu",
    "model": "opt-125m",
    "precision": "float32"
}

def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file, or return defaults if missing.
    
    Args:
        path: Path to config.yaml. If None, uses code/config.yaml.
    
    Returns:
        Configuration dictionary with seed, device, model, precision.
    """
    if path is None:
        path = Path("code/config.yaml")
    
    if not path.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(path, 'r') as f:
            loaded = yaml.safe_load(f)
            if loaded is None:
                return DEFAULT_CONFIG.copy()
            # Merge with defaults to ensure all keys present
            config = DEFAULT_CONFIG.copy()
            config.update(loaded)
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def get_config() -> Dict[str, Any]:
    """Get the current configuration.
    
    Returns:
        Configuration dictionary with seed, device, model, precision.
    """
    config_path = Path("code/config.yaml")
    return load_config(config_path)

def save_config(config: Dict[str, Any], path: Optional[Path] = None) -> None:
    """Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary to save.
        path: Path to write config.yaml. If None, uses code/config.yaml.
    """
    if path is None:
        path = Path("code/config.yaml")
    
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
