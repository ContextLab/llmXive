"""
Configuration management module for the molecular reactivity prediction pipeline.
Loads and validates configuration from src/modeling/config.yaml.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Default path relative to project root
DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"

_config_cache: Optional[Dict[str, Any]] = None

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to src/modeling/config.yaml.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the config file is not valid YAML.
    """
    global _config_cache
    
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
        
    # Resolve to absolute path to handle relative paths correctly
    config_path = Path(config_path).resolve()
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    # Check if we can use cached config (optional optimization)
    # For now, always reload to ensure fresh config if file changes
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    if config is None:
        raise ValueError(f"Configuration file is empty: {config_path}")
        
    return config

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific value from the configuration.
    
    Args:
        key: Dot-separated key path (e.g., 'data.raw_dir').
        default: Default value if key is not found.
        
    Returns:
        The configuration value or default.
    """
    config = load_config()
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate that the configuration has required sections.
    
    Args:
        config: The configuration dictionary to validate.
        
    Returns:
        True if valid, raises ValueError otherwise.
    """
    required_sections = ['project', 'data', 'modeling']
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    return True

def save_config(config: Dict[str, Any], config_path: Optional[Path] = None) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: The configuration dictionary to save.
        config_path: Path to save the config file. Defaults to src/modeling/config.yaml.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
        
    config_path = Path(config_path).resolve()
    
    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

# Convenience function to get the full config path
def get_config_path() -> Path:
    """Return the default configuration file path."""
    return DEFAULT_CONFIG_PATH.resolve()