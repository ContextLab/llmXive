import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Default configuration paths
CONFIG_PATH = Path("config.yaml")

# Global config store
_config: Optional[Dict[str, Any]] = None

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    global _config
    if _config is not None:
        return _config
    
    path = Path(config_path) if config_path else CONFIG_PATH
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")
    
    with open(path, 'r') as f:
        _config = yaml.safe_load(f)
    
    return _config

def get_config() -> Dict[str, Any]:
    """Get the loaded configuration."""
    if _config is None:
        load_config()
    return _config

def get_path(config: Dict[str, Any], key: str) -> str:
    """Get a path from config, resolving relative to project root."""
    val = config.get(key)
    if not val:
        raise KeyError(f"Missing config key: {key}")
    
    # If relative, resolve from project root
    if not os.path.isabs(val):
        base = Path.cwd()
        return str(base / val)
    return val

def get_seed(config: Dict[str, Any], default: int = 42) -> int:
    """Get random seed."""
    return config.get("seed", default)

def get_hyperparameter(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a hyperparameter from the 'hyperparameters' section."""
    hp = config.get("hyperparameters", {})
    return hp.get(key, default)

def get_simulation_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Get simulation configuration."""
    return config.get("simulation", {})

def save_config(config: Dict[str, Any], path: Optional[Union[str, Path]] = None) -> None:
    """Save configuration to YAML file."""
    path = Path(path) if path else CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
