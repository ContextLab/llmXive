"""
Configuration management for the project.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    """Simple configuration manager."""
    
    def __init__(self):
        self._config = {
            'project_root': Path(__file__).parent.parent.parent,
            'data_dir': self._config.get('data_dir', 'data'),
            'log_level': 'INFO',
        }
        self._load_env()
    
    def _load_env(self):
        """Load configuration from environment variables."""
        for key, value in os.environ.items():
            if key.startswith('PROJ_'):
                self._config[key.lower()] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

def get_config() -> Config:
    """Get the global configuration instance."""
    return Config()
