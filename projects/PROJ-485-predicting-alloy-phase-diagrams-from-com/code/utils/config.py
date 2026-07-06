"""
Environment configuration management for data source URLs.
Implements Constitution Principle II by centralizing source verification.
"""
import os
from typing import Dict, Any, Optional
from .logging import get_logger, log_info, log_error, log_warning
from .error_codes import ErrorCode

logger = get_logger(__name__)

# Default configuration values matching project specs
DEFAULT_CONFIG = {
    "NIST_JANAF_URL": "https://janaf.nist.gov/tables",
    "SGTE_URL": "https://www.sgte.org/databases",
    "LOCAL_DATA_PATH": "data/raw",
    "OUTPUT_PROCESSED_PATH": "data/processed",
    "OUTPUT_ARTIFACTS_PATH": "data/artifacts",
    "STATE_PATH": "state/PROJ-485",
    "LOG_LEVEL": "INFO",
    "MAX_RETRIES": 3,
    "BACKOFF_FACTOR": 2.0,
    "TIMEOUT_SECONDS": 30
}

class ConfigManager:
    """
    Manages environment configuration for data sources.
    Ensures Constitution Principle II: Data source URLs are centrally managed and verified.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Optional path to YAML config file. If None, uses defaults + env vars.
        """
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self._load_from_env()
        if config_path:
            self._load_from_file(config_path)
        self._validate()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mapping = {
            "NIST_JANAF_URL": "NIST_JANAF_URL",
            "SGTE_URL": "SGTE_URL",
            "LOCAL_DATA_PATH": "LOCAL_DATA_PATH",
            "OUTPUT_PROCESSED_PATH": "OUTPUT_PROCESSED_PATH",
            "OUTPUT_ARTIFACTS_PATH": "OUTPUT_ARTIFACTS_PATH",
            "STATE_PATH": "STATE_PATH",
            "LOG_LEVEL": "LOG_LEVEL",
            "MAX_RETRIES": "MAX_RETRIES",
            "BACKOFF_FACTOR": "BACKOFF_FACTOR",
            "TIMEOUT_SECONDS": "TIMEOUT_SECONDS"
        }

        for config_key, env_key in env_mapping.items():
            value = os.getenv(env_key)
            if value is not None:
                # Convert numeric types
                if config_key in ("MAX_RETRIES", "TIMEOUT_SECONDS"):
                    try:
                        value = int(value)
                    except ValueError:
                        log_warning(f"Invalid integer for {env_key}, using default")
                        continue
                elif config_key == "BACKOFF_FACTOR":
                    try:
                        value = float(value)
                    except ValueError:
                        log_warning(f"Invalid float for {env_key}, using default")
                        continue
                self._config[config_key] = value
                log_info(f"Loaded {config_key} from environment")

    def _load_from_file(self, config_path: str) -> None:
        """Load configuration from a YAML file."""
        if not os.path.exists(config_path):
            log_warning(f"Config file not found: {config_path}, using defaults and env vars")
            return

        try:
            import yaml
            with open(config_path, 'r') as f:
                file_config = yaml.safe_load(f)
                if isinstance(file_config, dict):
                    self._config.update(file_config)
                    log_info(f"Loaded configuration from {config_path}")
        except ImportError:
            log_error("PyYAML not installed, cannot load config file")
        except Exception as e:
            log_error(f"Error loading config file {config_path}: {e}")

    def _validate(self) -> None:
        """Validate critical configuration values."""
        # Validate URLs are not empty
        for key in ["NIST_JANAF_URL", "SGTE_URL"]:
            if not self._config.get(key):
                log_warning(f"Critical URL {key} is missing or empty")

        # Validate paths exist or can be created
        for key in ["LOCAL_DATA_PATH", "OUTPUT_PROCESSED_PATH", "OUTPUT_ARTIFACTS_PATH", "STATE_PATH"]:
            path = self._config.get(key)
            if path and not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    log_info(f"Created directory: {path}")
                except Exception as e:
                    log_error(f"Failed to create directory {path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def get_required(self, key: str) -> Any:
        """
        Get a required configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value
            
        Raises:
            ValueError: If key is missing
        """
        value = self._config.get(key)
        if value is None:
            raise ValueError(f"Required configuration key missing: {key}")
        return value

    def get_source_urls(self) -> Dict[str, str]:
        """
        Get all configured data source URLs.
        
        Returns:
            Dictionary mapping source names to URLs
        """
        return {
            "NIST_JANAF": self.get("NIST_JANAF_URL"),
            "SGTE": self.get("SGTE_URL")
        }

    def is_source_available(self, source_name: str) -> bool:
        """
        Check if a data source URL is configured and non-empty.
        
        Args:
            source_name: Name of the source (e.g., "NIST_JANAF", "SGTE")
            
        Returns:
            True if URL is configured and non-empty, False otherwise
        """
        url = self.get(f"{source_name}_URL")
        return bool(url and url.strip())

# Global config instance
_global_config: Optional[ConfigManager] = None

def get_config(config_path: Optional[str] = None) -> ConfigManager:
    """
    Get the global configuration manager instance.
    
    Args:
        config_path: Optional path to config file for first initialization
        
    Returns:
        ConfigManager instance
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager(config_path)
    return _global_config

def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global _global_config
    _global_config = None

def validate_data_sources() -> bool:
    """
    Validate that all required data sources are configured.
    
    Returns:
        True if all sources are configured, False otherwise
    """
    config = get_config()
    sources = config.get_source_urls()
    all_valid = True
    
    for name, url in sources.items():
        if not url or not url.strip():
            log_error(f"Data source {name} URL is not configured")
            all_valid = False
        else:
            log_info(f"Data source {name} configured: {url[:50]}...")
    
    return all_valid
