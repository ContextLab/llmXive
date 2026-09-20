import os
import json
from typing import Dict, Any, Optional
from .logging import get_logger, log_info, log_error, log_warning
from .error_codes import ErrorCode

logger = get_logger(__name__)

class ConfigManager:
    """
    Manages configuration loading and validation for the alloy phase diagram project.
    Enforces Constitution Principle II by validating required schema keys.
    """

    def __init__(self, config_path: str = "code/config.yaml"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Loads the YAML configuration file."""
        try:
            import yaml
            if not os.path.exists(self.config_path):
                log_error(
                    self,
                    ErrorCode.DATA_SOURCE_MISSING,
                    f"Configuration file not found: {self.config_path}"
                )
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            
            log_info(self, "Configuration loaded successfully.")
        except yaml.YAMLError as e:
            log_error(
                self,
                ErrorCode.INVALID_DATA_SCHEMA,
                f"Failed to parse YAML configuration: {e}"
            )
            raise
        except Exception as e:
            log_error(
                self,
                ErrorCode.DATA_SOURCE_MISSING,
                f"Unexpected error loading configuration: {e}"
            )
            raise

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value by key."""
        return self._config.get(key, default)

    def validate_data_sources(self) -> bool:
        """
        Validates that required data source URLs and paths are present.
        Returns True if valid, raises an error with ErrorCode.DATA_SOURCE_MISSING if not.
        """
        required_keys = ["nist_janaf_url", "sgte_url", "local_fallback_path"]
        
        for key in required_keys:
            value = self._config.get(key)
            if value is None or (isinstance(value, str) and value.strip() == ""):
                msg = f"Required configuration key '{key}' is missing or empty."
                log_error(self, ErrorCode.DATA_SOURCE_MISSING, msg)
                raise ValueError(msg)
        
        log_info(self, "Data source configuration validated successfully.")
        return True

    def validate_data_schema(self) -> bool:
        """
        Validates the data_schema section for required phase boundary coordinates.
        Specifically checks for 'temperature' and 'composition' as required columns.
        """
        schema = self._config.get("data_schema", {})
        required_columns = schema.get("required_columns", [])
        
        required_coords = ["temperature", "composition"]
        missing = [coord for coord in required_coords if coord not in required_columns]
        
        if missing:
            msg = f"Data schema validation failed: Missing required phase boundary coordinates: {missing}"
            log_error(self, ErrorCode.INVALID_DATA_SCHEMA, msg)
            raise ValueError(msg)
        
        log_info(self, "Data schema validation passed (phase boundary coordinates present).")
        return True

    def validate_all(self) -> bool:
        """Runs all validation checks."""
        self.validate_data_sources()
        self.validate_data_schema()
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Returns the raw configuration dictionary."""
        return self._config.copy()


# Global config instance
_global_config: Optional[ConfigManager] = None

def get_config(config_path: str = "code/config.yaml") -> ConfigManager:
    """
    Returns the singleton ConfigManager instance.
    Creates it if it doesn't exist.
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager(config_path)
    return _global_config

def reset_config() -> None:
    """Resets the global config instance (useful for testing)."""
    global _global_config
    _global_config = None

def validate_data_sources(config: Optional[ConfigManager] = None) -> bool:
    """
    Convenience function to validate data sources.
    """
    if config is None:
        config = get_config()
    return config.validate_data_sources()
