"""
Configuration management module.

This module handles environment variables and file path configuration.
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """Configuration manager for the pipeline."""

    def __init__(self, env_prefix: str = "LLMXIVE_"):
        self.env_prefix = env_prefix
        self._config: Dict[str, Any] = {}
        self._load_env_vars()

    def _load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                config_key = key[len(self.env_prefix):].lower()
                self._config[config_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value


_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the singleton Config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
