import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config.yaml file.
        
    Returns:
        Dictionary containing the configuration.
        
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the YAML is invalid.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        try:
            config = yaml.safe_load(f)
            return config if config else {}
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML config: {e}")
            raise

def get_global_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract global configuration parameters.
    
    Args:
        config: Full configuration dictionary.
        
    Returns:
        Dictionary with global parameters.
    """
    return {
        "global_seed": config.get("global_seed"),
        "simulation_timeout_seconds": config.get("simulation_timeout_seconds", 3600)
    }

def validate_config_schema(config: Dict[str, Any]) -> bool:
    """
    Validate that the config has required keys.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        True if valid, False otherwise.
    """
    required_keys = ["global_seed"]
    for key in required_keys:
        if key not in config:
            logging.warning(f"Missing required config key: {key}")
            return False
    return True
