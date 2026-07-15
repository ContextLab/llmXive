"""
Configuration Management.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
import sys

from utils.logging import get_module_logger

logger = get_module_logger(__name__)

class ConfigError(Exception):
    pass

class Config:
    def __init__(self):
        self.paths = type('Paths', (), {
            'raw': 'data/raw',
            'processed': 'data/processed',
            'results': 'data/results',
            'figures': 'figures'
        })()
        self.seeds = {'default': 42}
        self.hyperparameters = {}
        self.verified_urls = {
            'genomic': None,
            'env': None,
            'compound': None
        }

_global_config: Optional[Config] = None

def load_config(path: Optional[Union[str, Path]] = None) -> Config:
    """Loads config from a YAML file or returns default."""
    global _global_config
    if _global_config:
        return _global_config

    config = Config()
    
    # Try to load from default location
    default_path = Path(__file__).parent.parent / "config" / "config.yaml"
    if path:
        default_path = Path(path)
    
    if default_path.exists():
        try:
            with open(default_path, 'r') as f:
                data = yaml.safe_load(f)
                if data:
                    # Update config attributes
                    if 'paths' in data:
                        for k, v in data['paths'].items():
                            setattr(config.paths, k, v)
                    if 'verified_urls' in data:
                        config.verified_urls.update(data['verified_urls'])
                    if 'seeds' in data:
                        config.seeds.update(data['seeds'])
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")
    
    _global_config = config
    return config

def get_config() -> Config:
    """Gets the global config, loading if necessary."""
    if _global_config is None:
        return load_config()
    return _global_config

def reset_config():
    """Resets the global config."""
    global _global_config
    _global_config = None

def main(*args, **kwargs):
    """Entry point for config script."""
    # Just load and print
    cfg = get_config()
    print(f"Config loaded: {cfg.paths.raw}")

if __name__ == "__main__":
    main()