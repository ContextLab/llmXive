"""
Configuration Management Module.

Handles loading of configuration from YAML files and provides
access to seeds, paths, hyperparameters, and verified URLs.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Configuration container."""
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from config."""
        return self._config.get(key, default)

    @property
    def verified_urls(self) -> Dict[str, str]:
        """Return verified URLs dict."""
        return self._config.get('verified_urls', {})

    @property
    def paths(self) -> Dict[str, str]:
        """Return paths dict."""
        return self._config.get('paths', {})

    @property
    def seeds(self) -> Dict[str, int]:
        """Return seeds dict."""
        return self._config.get('seeds', {})

_global_config: Optional[Config] = None

def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config file. Defaults to 'config.yaml' in project root.

    Returns:
        Config object.
    
    Raises:
        ConfigError: If file not found or invalid YAML.
    """
    if config_path is None:
        # Default to project root config.yaml
        config_path = Path("config.yaml")
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        # If no config file exists, create a minimal default one
        # This prevents crashes in CI/CI-like environments where config might be missing
        default_config = {
            "verified_urls": {
                "genomic": None,
                "env": None,
                "compound": None
            },
            "paths": {
                "raw": "data/raw",
                "processed": "data/processed",
                "results": "data/results"
            },
            "seeds": {
                "global": 42
            }
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f)
        logger = logging.getLogger(__name__)
        logger.warning(f"Created default config at {config_path}")
    
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ConfigError(f"Failed to load config file: {e}")

    return Config(data)

def get_config() -> Config:
    """
    Get the global configuration instance.
    Loads it if not already loaded.

    Returns:
        Global Config object.
    """
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config

def reset_config():
    """Reset global config (useful for testing)."""
    global _global_config
    _global_config = None

# Import logging here to avoid circular import issues during module load
import logging
logger = logging.getLogger(__name__)
