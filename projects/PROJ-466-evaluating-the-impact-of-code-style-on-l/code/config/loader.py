import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""
    pass

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML config file
        
    Returns:
        Dictionary containing configuration values
        
    Raises:
        ConfigError: If file not found or invalid YAML
    """
    path = Path(config_path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {config_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}")

def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that required configuration keys are present.
    
    Required top-level keys: seeds, thresholds, batch_size, timeout
    Required nested keys:
      - seeds: random, torch, numpy
      - thresholds: alpha, substantial_diff, min_pass_rate
      - batch_size: start, min, max
      - timeout: per_task_minutes, per_style_minutes, total_pipeline_minutes
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ConfigError: If any required key is missing
    """
    required_top_level = ['seeds', 'thresholds', 'batch_size', 'timeout']
    
    for key in required_top_level:
        if key not in config:
            raise ConfigError(f"Missing required config key: {key}")
    
    # Validate seeds
    required_seeds = ['random', 'torch', 'numpy']
    for seed_key in required_seeds:
        if seed_key not in config.get('seeds', {}):
            raise ConfigError(f"Missing required seeds.{seed_key}")
    
    # Validate thresholds
    required_thresholds = ['alpha', 'substantial_diff', 'min_pass_rate']
    for thresh_key in required_thresholds:
        if thresh_key not in config.get('thresholds', {}):
            raise ConfigError(f"Missing required thresholds.{thresh_key}")
    
    # Validate batch_size
    required_batch = ['start', 'min', 'max']
    for batch_key in required_batch:
        if batch_key not in config.get('batch_size', {}):
            raise ConfigError(f"Missing required batch_size.{batch_key}")
    
    # Validate timeout
    required_timeout = ['per_task_minutes', 'per_style_minutes', 'total_pipeline_minutes']
    for timeout_key in required_timeout:
        if timeout_key not in config.get('timeout', {}):
            raise ConfigError(f"Missing required timeout.{timeout_key}")

def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get a value from config using dot notation for nested keys.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path (e.g., "seeds.random")
        default: Default value if key not found
        
    Returns:
        The configuration value or default
    """
    keys = key_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value

def load_and_get(config_path: str, key_path: str, default: Any = None) -> Any:
    """
    Load config and get a value in one step.
    
    Args:
        config_path: Path to YAML config
        key_path: Dot-separated path to the value
        default: Default value if not found
        
    Returns:
        The configuration value or default
    """
    config = load_config(config_path)
    return get_config_value(config, key_path, default)

def load_config_with_defaults(config_path: str) -> Dict[str, Any]:
    """
    Load config with default values for missing keys.
    
    Args:
        config_path: Path to YAML config
        
    Returns:
        Configuration dictionary with defaults filled in
    """
    defaults = {
        'seeds': {
            'random': 42,
            'torch': 42,
            'numpy': 42
        },
        'thresholds': {
            'alpha': 0.05,
            'substantial_diff': 0.15,
            'min_pass_rate': 0.01
        },
        'batch_size': {
            'start': 50,
            'min': 1,
            'max': 256
        },
        'timeout': {
            'per_task_minutes': 5,
            'per_style_minutes': 30,
            'total_pipeline_minutes': 360
        }
    }
    
    config = load_config(config_path)
    
    # Merge defaults with loaded config
    merged = {**defaults}
    for key in merged:
        if key in config:
            if isinstance(merged[key], dict) and isinstance(config[key], dict):
                merged[key] = {**merged[key], **config[key]}
            else:
                merged[key] = config[key]
    
    return merged
