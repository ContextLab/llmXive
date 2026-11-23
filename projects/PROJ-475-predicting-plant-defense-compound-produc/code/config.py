"""
Configuration management module.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import sys
from utils.logging import get_module_logger

logger = get_module_logger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Configuration container class."""

    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        return key in self._config

_global_config: Optional[Config] = None

def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the configuration file. If None, uses default location.

    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        config_path = Path("config.yaml")
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}. Using defaults.")
        return {
            "seeds": {"default": 42},
            "paths": {
                "raw_data": "data/raw",
                "processed_data": "data/processed",
                "figures": "figures"
            },
            "hyperparameters": {},
            "verified_urls": {}
        }

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse config file: {e}")
    except IOError as e:
        raise ConfigError(f"Failed to read config file: {e}")

def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config instance.
    """
    global _global_config
    if _global_config is None:
        config_dict = load_config()
        _global_config = Config(config_dict)
    return _global_config

def reset_config() -> None:
    """Reset the global configuration (useful for testing)."""
    global _global_config
    _global_config = None

def main():
    """Main entry point for config module."""
    logger.info("Loading configuration...")
    config = get_config()
    logger.info(f"Configuration loaded: {config._config}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
