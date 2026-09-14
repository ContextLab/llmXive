"""
Configuration management for data source URLs and environment variables.
Implements Constitution Principle II: Verified Data Sources.
"""
import os
import json
from typing import Dict, Any, Optional
from .logging import get_logger, log_info, log_error, log_warning
from .error_codes import ErrorCode

logger = get_logger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "data_sources": {
        "nist_janaf_url": os.getenv(
            "NIST_JANAF_URL",
            "https://janaf.nist.gov/phase-diagrams"
        ),
        "sgte_url": os.getenv(
            "SGTE_URL",
            "https://sgte.org/thermodynamic-database"
        ),
        "local_fallback_path": os.getenv(
            "LOCAL_FALLBACK_PATH",
            "data/raw/phase_data.csv"
        )
    },
    "api": {
        "timeout_seconds": int(os.getenv("API_TIMEOUT_SECONDS", "30")),
        "max_retries": int(os.getenv("API_MAX_RETRIES", "3")),
        "backoff_factor": float(os.getenv("API_BACKOFF_FACTOR", "2.0"))
    },
    "validation": {
        "max_deviation_percent": float(os.getenv("MAX_DEVIATION_PERCENT", "1.0"))
    }
}

class ConfigManager:
    """
    Manages application configuration, loading from environment variables
    and optional configuration files.
    """

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = DEFAULT_CONFIG.copy()
            self._load_env_overrides()

    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        env_mapping = {
            "NIST_JANAF_URL": ("data_sources", "nist_janaf_url"),
            "SGTE_URL": ("data_sources", "sgte_url"),
            "LOCAL_FALLBACK_PATH": ("data_sources", "local_fallback_path"),
            "API_TIMEOUT_SECONDS": ("api", "timeout_seconds"),
            "API_MAX_RETRIES": ("api", "max_retries"),
            "API_BACKOFF_FACTOR": ("api", "backoff_factor"),
            "MAX_DEVIATION_PERCENT": ("validation", "max_deviation_percent")
        }

        for env_var, (section, key) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert types based on expected values
                if key in ["timeout_seconds", "max_retries"]:
                    try:
                        value = int(value)
                    except ValueError:
                        log_warning(f"Invalid integer for {env_var}, using default")
                        continue
                elif key in ["backoff_factor", "max_deviation_percent"]:
                    try:
                        value = float(value)
                    except ValueError:
                        log_warning(f"Invalid float for {env_var}, using default")
                        continue

                self._config[section][key] = value
                log_info(f"Loaded config override: {env_var}={value}")

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-separated path.

        Args:
            path: Dot-separated path to config value (e.g., "data_sources.nist_janaf_url")
            default: Default value if path doesn't exist

        Returns:
            Configuration value or default
        """
        keys = path.split(".")
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, path: str, value: Any):
        """
        Set a configuration value by dot-separated path.

        Args:
            path: Dot-separated path to config value
            value: Value to set
        """
        keys = path.split(".")
        current = self._config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
        log_info(f"Set config: {path}={value}")

    def validate_data_sources(self) -> bool:
        """
        Validate that required data source URLs are configured.
        Returns True if valid, False otherwise.
        """
        required_sources = [
            "data_sources.nist_janaf_url",
            "data_sources.sgte_url",
            "data_sources.local_fallback_path"
        ]

        all_valid = True
        for source_path in required_sources:
            value = self.get(source_path)
            if not value or value == "":
                log_error(f"Missing required config: {source_path}")
                all_valid = False
            elif not value.startswith(("http://", "https://", "/")):
                log_error(f"Invalid URL format for config: {source_path}")
                all_valid = False

        if all_valid:
            log_info("All data source URLs validated successfully")
        else:
            log_error("Data source validation failed")

        return all_valid

    def to_dict(self) -> Dict[str, Any]:
        """Return a copy of the full configuration dictionary."""
        return self._config.copy()

    def save_to_file(self, filepath: str):
        """Save current configuration to a JSON file."""
        try:
            with open(filepath, 'w') as f:
                json.dump(self._config, f, indent=2)
            log_info(f"Configuration saved to {filepath}")
        except Exception as e:
            log_error(f"Failed to save configuration: {e}")
            raise

# Global config instance
_config_instance: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    """Get the singleton ConfigManager instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance

def reset_config():
    """Reset the global config instance (useful for testing)."""
    global _config_instance
    ConfigManager._config = None
    _config_instance = None

def validate_data_sources() -> bool:
    """
    Convenience function to validate data source configuration.
    Returns True if valid, False otherwise.
    """
    config = get_config()
    return config.validate_data_sources()