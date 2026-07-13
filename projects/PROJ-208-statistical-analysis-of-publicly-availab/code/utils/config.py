"""
Configuration manager for llmXive pipeline.

Handles random seeds, paths, thresholds, and API configurations.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import yaml

class Config:
    """Central configuration class."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.cwd() / "config.yaml"
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file or use defaults."""
        defaults = {
            'random_seeds': {
                'python': 42,
                'numpy': 42,
                'global': 42
            },
            'paths': {
                'project_root': str(Path.cwd()),
                'data_raw': 'data/raw',
                'data_processed': 'data/processed',
                'data_figures': 'data/figures',
                'data_logs': 'data/logs',
                'code': 'code',
                'tests': 'tests',
                'state': 'state',
                'contracts': 'contracts'
            },
            'thresholds': {
                'min_completeness': 0.95,
                'max_error_rate': 0.05,
                'min_repositories': 100,
                'min_issues': 1000
            },
            'api': {
                'rate_limit_delay': 1.0,
                'max_retries': 5,
                'backoff_factor': 2.0
            },
            'advancement': {
                'advancement_thresholds': {
                    'min_completeness': 0.95,
                    'max_error_rate': 0.05,
                    'required_fields': ['checksum', 'timestamp', 'artifact_path']
                }
            }
        }
        
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                file_config = yaml.safe_load(f) or {}
                # Deep merge defaults with file config
                for key, value in file_config.items():
                    if isinstance(value, dict) and key in defaults and isinstance(defaults[key], dict):
                        defaults[key].update(value)
                    else:
                        defaults[key] = value
        
        return defaults
    
    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save current configuration to YAML file."""
        path = config_path or self.config_path
        with open(path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value by dot-separated key."""
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

# Global config instance
_config_instance: Optional[Config] = None

def get_config(config_path: Optional[Path] = None) -> Config:
    """Get or create the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(config_path)
    return _config_instance

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = get_config().get('random_seeds.global', 42)
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Try to set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_path(key: str, base: Optional[Path] = None) -> Path:
    """Get a path from configuration."""
    config = get_config()
    path_str = config.get(f'paths.{key}', key)
    base = base or Path(config.get('paths.project_root', '.'))
    return base / path_str

def get_threshold(key: str) -> float:
    """Get a threshold value from configuration."""
    return get_config().get(f'thresholds.{key}', 0.0)

def get_api_config(key: str) -> Any:
    """Get an API configuration value."""
    return get_config().get(f'api.{key}', None)

def save_config(config_path: Optional[Path] = None) -> None:
    """Save the global configuration."""
    get_config().save_config(config_path)

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration and return as dict."""
    config = Config(config_path)
    return config._config
