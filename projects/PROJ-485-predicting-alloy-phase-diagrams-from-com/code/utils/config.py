import os
import yaml
import json
from typing import Dict, Any, Optional
from .logging import get_logger, log_info, log_error
from .error_codes import ErrorCode

class ConfigManager:
    _config = {}

    @classmethod
    def load(cls, path: str = "code/config.yaml"):
        if not os.path.exists(path):
            log_error(f"Config file not found: {path}")
            return False
        try:
            with open(path, 'r') as f:
                cls._config = yaml.safe_load(f)
            log_info(f"Config loaded from {path}")
            return True
        except Exception as e:
            log_error(f"Failed to load config: {e}")
            return False

    @classmethod
    def get(cls, key: str, default: Any = None):
        keys = key.split('.')
        val = cls._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    @classmethod
    def get_config(cls):
        return cls._config

    @classmethod
    def validate_data_sources(cls):
        # Check for required keys
        required = ['nist_janaf_url', 'sgte_url', 'local_fallback_path', 'data_schema']
        for key in required:
            if key not in cls._config:
                log_error(f"Missing required config key: {key}")
                return False
        return True

    @classmethod
    def reset(cls):
        cls._config = {}

def get_config():
    return ConfigManager.get_config()

def validate_data_sources():
    return ConfigManager.validate_data_sources()

def reset_config():
    ConfigManager.reset()
