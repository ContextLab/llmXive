"""
Configuration management module.
"""
import os
import sys
import yaml
import json
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logging import get_logger, log_info, log_error
from utils.error_codes import ErrorCode

logger = get_logger(__name__)

_config_cache = None

def get_config(filepath: str = "code/config.yaml") -> Dict[str, Any]:
    """Load and return configuration."""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    if not os.path.exists(filepath):
        log_error(logger, f"Config file not found: {filepath}")
        raise FileNotFoundError(f"Config file not found: {filepath}")

    with open(filepath, 'r') as f:
        config = yaml.safe_load(f)

    _config_cache = config
    return config

def validate_data_sources(config: Dict) -> bool:
    """Validate that data sources are configured."""
    nist_url = config.get("nist_janaf_url", "")
    sgte_url = config.get("sgte_url", "")
    local_path = config.get("local_fallback_path", "")

    if not nist_url and not sgte_url and not local_path:
        log_error(logger, f"{ErrorCode.DATA_SOURCE_MISSING.value}: No data sources configured")
        return False

    return True

def reset_config():
    """Reset configuration cache."""
    global _config_cache
    _config_cache = None

class ConfigManager:
    """Configuration manager class."""

    def __init__(self, filepath: str = "code/config.yaml"):
        self.filepath = filepath
        self.config = get_config(filepath)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def validate(self) -> bool:
        """Validate the configuration."""
        return validate_data_sources(self.config)
