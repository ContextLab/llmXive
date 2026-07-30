import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)

class ConfigError(Exception):
    pass

class Settings:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._validate()

    def _validate(self):
        required_keys = ['gpr_max_runtime', 'gpr_max_memory', 'ocr_enabled']
        for key in required_keys:
            if key not in self.config:
                raise ConfigError(f"Missing required config key: {key}")
        
        if not isinstance(self.config['gpr_max_runtime'], (int, float)):
            raise ConfigError("gpr_max_runtime must be a number")
        if not isinstance(self.config['gpr_max_memory'], (int, float)):
            raise ConfigError("gpr_max_memory must be a number")
        if not isinstance(self.config['ocr_enabled'], bool):
            raise ConfigError("ocr_enabled must be a boolean")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

_settings_instance: Optional[Settings] = None

def load_config(config_path: Optional[str] = None) -> Settings:
    """
    Loads and validates the configuration file.
    """
    global _settings_instance
    if _settings_instance is not None:
        return _settings_instance

    if config_path is None:
        config_path = os.getenv("CONFIG_PATH", "code/src/config/config.yaml")
    
    path = Path(config_path)
    if not path.exists():
        # Create a default config if it doesn't exist
        logger.warning(f"Config file {config_path} not found. Creating default.")
        path.parent.mkdir(parents=True, exist_ok=True)
        default_config = {
            "gpr_max_runtime": 1800,
            "gpr_max_memory": 5.0,
            "ocr_enabled": False,
            "api_endpoints": {},
            "resource_limits": {},
            "ocr": {},
            "data_paths": {}
        }
        with open(path, 'w') as f:
            yaml.dump(default_config, f)
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    _settings_instance = Settings(config)
    return _settings_instance

def get_settings() -> Settings:
    if _settings_instance is None:
        return load_config()
    return _settings_instance

def reset_settings():
    global _settings_instance
    _settings_instance = None

def get_config_value(key: str) -> Any:
    settings = get_settings()
    return settings.get(key)

def get_resource_limits() -> Dict[str, float]:
    settings = get_settings()
    return {
        "max_runtime": settings.get("gpr_max_runtime"),
        "max_memory": settings.get("gpr_max_memory")
    }

def get_api_endpoints() -> Dict[str, str]:
    settings = get_settings()
    return settings.get("api_endpoints", {})

def get_ocr_settings() -> Dict[str, Any]:
    settings = get_settings()
    return settings.get("ocr", {})

def get_data_paths() -> Dict[str, str]:
    settings = get_settings()
    return settings.get("data_paths", {})

def create_default_config(path: str = "code/src/config/config.yaml"):
    """Creates a default config file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    config = {
        "gpr_max_runtime": 1800,
        "gpr_max_memory": 5.0,
        "ocr_enabled": False,
        "api_endpoints": {},
        "resource_limits": {},
        "ocr": {},
        "data_paths": {}
    }
    with open(p, 'w') as f:
        yaml.dump(config, f)
    logger.info(f"Created default config at {path}")