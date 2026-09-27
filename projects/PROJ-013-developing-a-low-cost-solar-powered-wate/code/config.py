import os
from pathlib import Path
from typing import Optional, Dict, Any
from utils import get_project_root, ProjectError, setup_logging

# Initialize logger for this module
logger = setup_logging(__name__)

class Config:
    """
    Central configuration class for the project.
    Loads settings from code/config.yaml and environment variables.
    """
    def __init__(self, config_path: Optional[Path] = None):
        self.project_root = get_project_root()
        self._config_path = config_path or self.project_root / "config.yaml"
        self._config_data: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML and environment variables."""
        try:
            import yaml
            if self._config_path.exists():
                with open(self._config_path, 'r') as f:
                    self._config_data = yaml.safe_load(f) or {}
                logger.info(f"Loaded config from {self._config_path}")
            else:
                logger.warning(f"Config file not found at {self._config_path}, using defaults.")
        except ImportError:
            logger.warning("PyYAML not installed. Using empty config.")
            self._config_data = {}
        except Exception as e:
            raise ProjectError(f"Failed to load config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value."""
        return self._config_data.get(key, default)

# Global instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Get the singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config() -> Config:
    """Force reload of the configuration."""
    global _config_instance
    _config_instance = Config()
    return _config_instance

def get_nasa_power_key() -> str:
    """
    Retrieve the NASA POWER API key.
    
    Priority:
    1. Environment variable NASA_POWER_API_KEY
    2. Config file key 'nasa_power.api_key'
    
    Raises:
        ProjectError: If the key cannot be found.
    """
    # 1. Check environment variable (highest priority)
    api_key = os.getenv("NASA_POWER_API_KEY")
    if api_key:
        logger.debug("NASA POWER key loaded from environment variable.")
        return api_key

    # 2. Check config file
    config = get_config()
    api_key = config.get("nasa_power", {}).get("api_key")
    
    if api_key:
        logger.debug("NASA POWER key loaded from config file.")
        return api_key

    # 3. Fail loud if not found
    raise ProjectError(
        "NASA POWER API key not found. "
        "Please set the environment variable NASA_POWER_API_KEY "
        "or add 'nasa_power.api_key' to your config.yaml file."
    )
