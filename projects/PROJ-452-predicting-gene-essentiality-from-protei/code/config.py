"""
Configuration loader for the llmXive pipeline.

Loads organism IDs, confidence thresholds, and paths from a YAML configuration file.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Optional path to the config file. Defaults to 'config.yaml' in project root.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        ConfigError: If the file cannot be read or parsed.
    """
    if config_path is None:
        config_path = "config.yaml"
    
    path = Path(config_path)
    
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML configuration: {e}")
    except IOError as e:
        raise ConfigError(f"Failed to read configuration file: {e}")

def get_organisms(config: Optional[Dict[str, Any]] = None) -> List[str]:
    """
    Get the list of target organisms from the configuration.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        List of organism names (e.g., ['yeast', 'human']).
        
    Raises:
        ConfigError: If organisms are not defined.
    """
    if config is None:
        config = load_config()
    
    organisms = config.get('organisms', [])
    if not organisms:
        raise ConfigError("No organisms defined in configuration.")
    
    return organisms

def get_confidence_thresholds(config: Optional[Dict[str, Any]] = None) -> List[int]:
    """
    Get the list of confidence thresholds from the configuration.
    
    Args:
        config: Optional pre-loaded config dict.
        
    Returns:
        List of integer thresholds (e.g., [500, 700, 900]).
        
    Raises:
        ConfigError: If thresholds are not defined.
    """
    if config is None:
        config = load_config()
    
    thresholds = config.get('confidence_thresholds', [])
    if not thresholds:
        raise ConfigError("No confidence thresholds defined in configuration.")
    
    return [int(t) for t in thresholds]

def get_path(key: str) -> Path:
    """
    Resolve a path key from the configuration to an absolute Path.
    
    Args:
        key: The key name in the 'paths' section (e.g., 'data', 'results').
        
    Returns:
        Absolute Path object.
        
    Raises:
        ConfigError: If the path key is missing.
    """
    config = load_config()
    paths = config.get('paths', {})
    
    if key not in paths:
        # Default fallback if not explicitly defined but common keys exist
        if key == 'data':
            return Path('data')
        elif key == 'results':
            return Path('results')
        elif key == 'state':
            return Path('state')
        elif key == 'code':
            return Path('code')
        elif key == 'tests':
            return Path('tests')
        else:
            raise ConfigError(f"Path key '{key}' not found in configuration.")
    
    path_str = paths[key]
    return Path(path_str)

def ensure_dirs(*paths: Path) -> None:
    """
    Ensure that the given directories exist, creating them if necessary.
    
    Args:
        *paths: Variable number of Path objects to ensure exist.
    """
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)

def get_full_config() -> Dict[str, Any]:
    """
    Load and return the full configuration dictionary.
    
    Returns:
        Full configuration dict.
    """
    return load_config()
