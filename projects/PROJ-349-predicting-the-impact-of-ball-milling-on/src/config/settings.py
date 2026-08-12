"""
Configuration management for the ball milling prediction pipeline.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)


class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass


class Settings:
    """Settings container for the application."""
    
    def __init__(self, config: Dict[str, Any]):
        self._config = config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value by key (dot notation supported)."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def get_resource_limits(self) -> Dict[str, float]:
        """Get GPR resource limits."""
        return {
            "max_runtime": self.get("gpr_max_runtime", 1800.0),
            "max_memory": self.get("gpr_max_memory", 5.0)
        }
    
    def get_ocr_settings(self) -> Dict[str, Any]:
        """Get OCR fallback settings."""
        return {
            "fallback_enabled": self.get("ocr.fallback_enabled", False)
        }
    
    def get_data_paths(self) -> Dict[str, Path]:
        """Get data directory paths."""
        return {
            "raw": Path(self.get("data.raw_dir", "data/raw")),
            "processed": Path(self.get("data.processed_dir", "data/processed")),
            "splits": Path(self.get("data.splits_dir", "data/splits")),
            "results": Path(self.get("data.results_dir", "results"))
        }
    
    def get_api_endpoints(self) -> Dict[str, str]:
        """Get API endpoint URLs."""
        return {
            "materials_project": self.get("api.materials_project", "https://next-gen.materialsproject.org/api/v2/materials"),
            "nist": self.get("api.nist", "https://www.nist.gov/pml/atomic-spectra-database")
        }
    
    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys from config or environment."""
        keys = {}
        # Materials Project
        keys["materials_project"] = self.get("api_keys.materials_project") or os.getenv("MP_API_KEY")
        # NIST (if needed)
        keys["nist"] = self.get("api_keys.nist") or os.getenv("NIST_API_KEY")
        return keys

    @property
    def config(self) -> Dict[str, Any]:
        """Get the raw config dictionary."""
        return self._config


_settings: Optional[Settings] = None


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config file. If None, uses default path.

    Returns:
        Configuration dictionary.

    Raises:
        ConfigError: If config file is missing required keys.
    """
    if config_path is None:
        config_path = "config.yaml"
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Config file not found: {config_file}. Using defaults.")
        return _get_default_config()
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse config file: {e}")
    
    # Validate required keys
    _validate_config(config)
    
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate that required config keys exist and are of correct type."""
    required_keys = [
        "gpr_max_runtime",
        "gpr_max_memory",
        "ocr.fallback_enabled"
    ]
    
    for key in required_keys:
        keys = key.split(".")
        value = config
        found = True
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                found = False
                break
        
        if not found:
            logger.warning(f"Missing required config key: {key}. Using default.")


def _get_default_config() -> Dict[str, Any]:
    """Return default configuration values."""
    return {
        "gpr_max_runtime": 1800.0,
        "gpr_max_memory": 5.0,
        "ocr": {
            "fallback_enabled": False
        },
        "data": {
            "raw_dir": "data/raw",
            "processed_dir": "data/processed",
            "splits_dir": "data/splits",
            "results_dir": "results"
        },
        "api": {
            "materials_project": "https://next-gen.materialsproject.org/api/v2/materials",
            "nist": "https://www.nist.gov/pml/atomic-spectra-database"
        },
        "api_keys": {
            "materials_project": None,
            "nist": None
        }
    }


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        config = load_config()
        _settings = Settings(config)
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance."""
    global _settings
    _settings = None


def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value by key."""
    return get_settings().get(key, default)


def get_resource_limits() -> Dict[str, float]:
    """Get GPR resource limits."""
    return get_settings().get_resource_limits()


def get_api_endpoints() -> Dict[str, str]:
    """Get API endpoint URLs."""
    return get_settings().get_api_endpoints()


def get_ocr_settings() -> Dict[str, Any]:
    """Get OCR settings."""
    return get_settings().get_ocr_settings()


def get_data_paths() -> Dict[str, Path]:
    """Get data directory paths."""
    return get_settings().get_data_paths()


def create_default_config(output_path: str = "config.yaml") -> None:
    """Create a default configuration file."""
    config = _get_default_config()
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False)
    logger.info(f"Created default config file: {output_path}")
