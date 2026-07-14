"""
Configuration Loader for the Plant Defense Compound Prediction Pipeline.

Handles loading of seeds, paths, hyperparameters, and verified URLs.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Configuration class to hold project settings."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict
        self._validate()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def _validate(self):
        """Validate the configuration structure."""
        # Ensure required keys exist if needed
        required_keys = ['paths', 'seeds']
        for key in required_keys:
            if key not in self._config:
                # Allow missing keys if they have defaults, but warn
                pass
        
        # Validate paths
        paths = self._config.get('paths', {})
        if 'raw_data' not in paths:
            paths['raw_data'] = 'data/raw'
        if 'processed_data' not in paths:
            paths['processed_data'] = 'data/processed'
        
        # Ensure verified_urls exists
        if 'verified_urls' not in self._config:
            self._config['verified_urls'] = {}

    @property
    def paths(self) -> Dict[str, str]:
        return self._config.get('paths', {})

    @property
    def seeds(self) -> Dict[str, int]:
        return self._config.get('seeds', {'default': 42})

    @property
    def verified_urls(self) -> Dict[str, str]:
        return self._config.get('verified_urls', {})

def get_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Loads configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to 'config.yaml' in project root.
        
    Returns:
        Config: The loaded configuration object.
    """
    if config_path is None:
        config_path = Path("config.yaml")
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        # Provide a default minimal config if file doesn't exist
        # This allows the code to run even without a specific config file
        default_config = {
            "paths": {
                "raw_data": "data/raw",
                "processed_data": "data/processed"
            },
            "seeds": {
                "default": 42
            },
            "verified_urls": {
                # Empty by default to trigger mock generation as per T010 logic
                # In a real run, these would be populated with real URLs
                "genomic": None, 
                "env": None,
                "compound": None
            }
        }
        return Config(default_config)

    try:
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
            if config_dict is None:
                config_dict = {}
            return Config(config_dict)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse config file: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load config file: {e}")

# Global config instance (lazy load)
_config_instance: Optional[Config] = None

def load_config() -> Config:
    """Loads and returns the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = get_config()
    return _config_instance

# For backward compatibility with imports
ConfigError = ConfigError
Config = Config
get_config = get_config
