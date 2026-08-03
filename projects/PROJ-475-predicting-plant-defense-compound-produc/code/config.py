import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import sys
from utils.logging import get_module_logger

logger = get_module_logger(__name__)

class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass

class Config:
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict
        self.paths = self._config.get('paths', {})
        self.seeds = self._config.get('seeds', {})
        self.hyperparameters = self._config.get('hyperparameters', {})
        self.verified_urls = self._config.get('verified_urls', {})
        
        # Ensure paths are Path objects
        if 'raw_data' in self.paths:
            self.paths['raw_data'] = Path(self.paths['raw_data'])
        if 'processed_data' in self.paths:
            self.paths['processed_data'] = Path(self.paths['processed_data'])
        if 'figures' in self.paths:
            self.paths['figures'] = Path(self.paths['figures'])

_global_config: Optional[Config] = None

def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Loads configuration from a YAML file."""
    global _global_config
    
    if config_path is None:
        # Default config path
        config_path = Path(__file__).parent.parent / "config" / "project_config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        _global_config = Config(config_dict)
        logger.info(f"Loaded configuration from {config_path}")
        return _global_config
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing configuration file: {e}")

def get_config() -> Config:
    """Returns the global configuration instance."""
    global _global_config
    if _global_config is None:
        # Try to load default config if not loaded
        try:
            return load_config()
        except ConfigError:
            # If no config file exists, raise error
            raise ConfigError("Configuration not loaded and no default config file found.")
    return _global_config

def reset_config():
    """Resets the global configuration."""
    global _global_config
    _global_config = None
    logger.info("Configuration reset.")

def main():
    """Main function for config module."""
    try:
        config = load_config()
        print("Configuration loaded successfully:")
        print(f"  Paths: {config.paths}")
        print(f"  Seeds: {config.seeds}")
        print(f"  Verified URLs: {config.verified_urls}")
    except ConfigError as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
