import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads the configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to 'config.yaml' in the project root.
                
    Returns:
        Dictionary containing the configuration.
    """
    if config_path is None:
        # Default to config.yaml in the same directory as this script or project root
        config_path = Path(__file__).parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config is None:
                config = {}
            return config
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing YAML config: {e}")

def get_organisms(config: Dict[str, Any]) -> List[str]:
    """Retrieves the list of organisms from config."""
    return config.get('organisms', [])

def get_confidence_thresholds(config: Dict[str, Any]) -> List[int]:
    """Retrieves the list of confidence thresholds from config."""
    return config.get('confidence_thresholds', [700])

def get_path(config: Dict[str, Any], key: str) -> Path:
    """
    Resolves a path from the config.
    
    Args:
        config: Configuration dictionary.
        key: Key in the 'paths' section of the config.
                
    Returns:
        Resolved Path object.
    """
    base_paths = config.get('paths', {})
    relative_path = base_paths.get(key, key) # Fallback to key if not found in paths
    # Assume project root is parent of code/
    project_root = Path(__file__).parent.parent
    return project_root / relative_path

def ensure_dirs(config: Dict[str, Any], path_key: str) -> None:
    """Ensures the directory for a given path key exists."""
    path = get_path(config, path_key)
    path.mkdir(parents=True, exist_ok=True)

def get_full_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Returns the full configuration dictionary."""
    return config