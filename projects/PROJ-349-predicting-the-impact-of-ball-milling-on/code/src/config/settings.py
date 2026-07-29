"""
Configuration settings loader for the project.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from src.utils.logger import get_module_logger
from src.utils.exceptions import DataIngestionError

logger = get_module_logger(__name__)

CONFIG_PATH = Path("src/config/config.yaml")

class ConfigError(Exception):
    """Raised when configuration loading fails."""
    pass

class Settings:
    """Singleton settings manager."""
    _instance: Optional['Settings'] = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self) -> None:
        """Load configuration from config.yaml."""
        if not CONFIG_PATH.exists():
            logger.warning(f"Config file not found at {CONFIG_PATH}. Creating default.")
            self._config = {
                "gpr_max_runtime": 1800,
                "gpr_max_memory": 5.0,
                "ocr_enabled": False,
                "api_endpoints": {},
                "data_paths": {}
            }
            self._save_default_config()
        else:
            try:
                with open(CONFIG_PATH, 'r') as f:
                    self._config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ConfigError(f"Failed to parse config.yaml: {e}")

        # Validate required keys
        required_keys = ["gpr_max_runtime", "gpr_max_memory", "ocr_enabled"]
        for key in required_keys:
            if key not in self._config:
                logger.warning(f"Missing required config key: {key}. Using default.")
                if key == "gpr_max_runtime":
                    self._config[key] = 1800
                elif key == "gpr_max_memory":
                    self._config[key] = 5.0
                elif key == "ocr_enabled":
                    self._config[key] = False

    def _save_default_config(self) -> None:
        """Save a default config file."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(self._config, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self._config.get(key, default)

    def get_resource_limits(self) -> Dict[str, float]:
        """Get GPR resource limits."""
        return {
            "max_runtime": self._config.get("gpr_max_runtime", 1800),
            "max_memory": self._config.get("gpr_max_memory", 5.0)
        }

    def get_ocr_settings(self) -> Dict[str, bool]:
        """Get OCR settings."""
        return {
            "ocr_enabled": self._config.get("ocr_enabled", False)
        }

def get_settings() -> Settings:
    """Get the global settings instance."""
    return Settings()

def reset_settings() -> None:
    """Reset the global settings instance."""
    Settings._instance = None
    Settings._config = {}

def load_config() -> Dict[str, Any]:
    """
    Load and return the configuration dictionary.
    This is a convenience function for tasks that need a direct dict.
    """
    settings = get_settings()
    return settings._config

def get_config_value(key: str) -> Any:
    """Get a specific config value."""
    return get_settings().get(key)

def get_resource_limits() -> Dict[str, float]:
    """Get resource limits."""
    return get_settings().get_resource_limits()

def get_api_endpoints() -> Dict[str, str]:
    """Get API endpoints."""
    return get_settings().get("api_endpoints", {})

def get_ocr_settings() -> Dict[str, bool]:
    """Get OCR settings."""
    return get_settings().get_ocr_settings()

def get_data_paths() -> Dict[str, str]:
    """Get data paths."""
    return get_settings().get("data_paths", {})

def create_default_config() -> None:
    """Create a default config file if it doesn't exist."""
    if not CONFIG_PATH.exists():
        Settings().load_config()
