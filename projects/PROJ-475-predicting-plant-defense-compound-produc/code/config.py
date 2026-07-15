"""
Configuration management for the Plant Defense Compound Prediction Pipeline.

This module handles loading, validation, and access to project configuration
including paths, hyperparameters, and verified URLs.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import sys

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Configuration container class."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict
        self._validate()
    
    def _validate(self):
        """Validate configuration structure."""
        required_sections = ['paths', 'hyperparameters', 'verified_urls', 'seeds']
        for section in required_sections:
            if section not in self._config:
                raise ConfigError(f"Missing required configuration section: {section}")
        
        # Validate paths
        if not isinstance(self._config['paths'], dict):
            raise ConfigError("paths must be a dictionary")
        
        # Validate verified_urls
        if not isinstance(self._config['verified_urls'], dict):
            raise ConfigError("verified_urls must be a dictionary")
    
    @property
    def paths(self) -> Dict[str, str]:
        return self._config['paths']
    
    @property
    def hyperparameters(self) -> Dict[str, Any]:
        return self._config['hyperparameters']
    
    @property
    def verified_urls(self) -> Dict[str, str]:
        return self._config['verified_urls']
    
    @property
    def seeds(self) -> Dict[str, int]:
        return self._config['seeds']
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self._config

# Global configuration instance
_config_instance: Optional[Config] = None

def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file. If None, uses default location.
        
    Returns:
        Config object
    """
    global _config_instance
    
    if config_path is None:
        # Default config location
        config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        _config_instance = Config(config_dict)
        return _config_instance
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse configuration file: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load configuration: {e}")

def get_config() -> Config:
    """
    Get the current configuration instance.
    
    Returns:
        Config object
        
    Raises:
        ConfigError: If configuration has not been loaded yet
    """
    global _config_instance
    
    if _config_instance is None:
        # Try to load from default location
        try:
            return load_config()
        except ConfigError:
            # If no config file exists, create a default one
            _config_instance = _create_default_config()
    
    return _config_instance

def reset_config():
    """Reset the configuration instance."""
    global _config_instance
    _config_instance = None

def _create_default_config() -> Config:
    """Create a default configuration if none exists."""
    default_config = {
        'paths': {
            'project_root': str(Path(__file__).parent.parent),
            'raw_data': str(Path(__file__).parent.parent / 'data' / 'raw'),
            'processed_data': str(Path(__file__).parent.parent / 'data' / 'processed'),
            'results': str(Path(__file__).parent.parent / 'data' / 'results'),
            'figures': str(Path(__file__).parent.parent / 'figures'),
            'state': str(Path(__file__).parent.parent / 'state'),
            'specs': str(Path(__file__).parent.parent / 'specs')
        },
        'hyperparameters': {
            'random_seed': 42,
            'test_size': 0.2,
            'cv_folds': 5,
            'lasso_alpha': 0.1,
            'ridge_alpha': 1.0
        },
        'verified_urls': {
            'genomic': '',  # Empty by default, will trigger mock generation
            'env': '',
            'compound': ''
        },
        'seeds': {
            'genomic': 42,
            'env': 123,
            'compound': 456
        }
    }
    
    return Config(default_config)

def main():
    """Main entry point for config module testing."""
    try:
        config = get_config()
        print("Configuration loaded successfully:")
        print(f"  Project root: {config.paths['project_root']}")
        print(f"  Raw data: {config.paths['raw_data']}")
        print(f"  Verified URLs: {config.verified_urls}")
        return 0
    except ConfigError as e:
        print(f"Configuration error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
