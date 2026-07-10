"""
Configuration loader for project constants.
Loads from src/config/constants.yaml.
"""
import yaml
import os

_config = None

def get_config():
    """
    Loads and returns the configuration dictionary.
    Caches the result on first call.
    """
    global _config
    if _config is not None:
        return _config
    
    config_path = os.path.join(os.path.dirname(__file__), 'constants.yaml')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        _config = yaml.safe_load(f)
    
    return _config
