import os
from pathlib import Path
from typing import Optional, Dict, Any
from utils import get_project_root, ProjectError, setup_logging

# Import dotenv if available, otherwise warn and use os.environ
try:
    from dotenv import load_dotenv
    _HAS_DOTENV = True
except ImportError:
    _HAS_DOTENV = False
    import logging
    logging.getLogger(__name__).warning(
        "python-dotenv not installed. .env files will be ignored. "
        "Install with: pip install python-dotenv"
    )

class Config:
    """
    Centralized configuration manager for the project.
    Loads settings from code/config.yaml (if exists) and environment variables.
    Supports .env file loading for API keys (e.g., NASA POWER).
    """

    def __init__(self, config_path: Optional[Path] = None):
        self._logger = setup_logging(__name__)
        self.project_root = get_project_root()
        
        # Default paths
        if config_path is None:
            self.config_path = self.project_root / "code" / "config.yaml"
        else:
            self.config_path = Path(config_path)

        # Load .env if available
        self._load_env()

        # Load YAML config if available
        self._config_data = self._load_yaml_config()

        # Expose common keys for convenience
        self.nasa_power_api_key = os.getenv("NASA_POWER_API_KEY", "")
        self.simulation_params = self._config_data.get("simulation", {})
        self.data_paths = self._config_data.get("data_paths", {})

    def _load_env(self) -> None:
        """Load environment variables from .env file in project root."""
        env_path = self.project_root / ".env"
        if env_path.exists():
            if _HAS_DOTENV:
                load_dotenv(env_path)
                self._logger.info(f"Loaded environment variables from {env_path}")
            else:
                self._logger.warning(
                    f".env file found at {env_path} but python-dotenv is not installed. "
                    "Variables will not be loaded."
                )
        else:
            self._logger.debug(f"No .env file found at {env_path}")

    def _load_yaml_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            self._logger.warning(f"Config file not found at {self.config_path}. Using defaults.")
            return {}

        try:
            import yaml
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f) or {}
            self._logger.info(f"Loaded configuration from {self.config_path}")
            return data
        except yaml.YAMLError as e:
            raise ProjectError(f"Failed to parse config file {self.config_path}: {e}")
        except Exception as e:
            raise ProjectError(f"Failed to load config file {self.config_path}: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key."""
        keys = key.split(".")
        value = self._config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value (in-memory only)."""
        keys = key.split(".")
        current = self._config_data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value

# Global instance
_global_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def reload_config() -> Config:
    """Reload the global configuration instance."""
    global _global_config
    _global_config = Config()
    return _global_config

# Helper to access NASA POWER key specifically
def get_nasa_power_key() -> str:
    """Retrieve the NASA POWER API key from environment or config."""
    cfg = get_config()
    # Priority: Env var > Config file > Empty string
    key = os.getenv("NASA_POWER_API_KEY")
    if key:
        return key
    return cfg.get("api_keys.nasa_power", "")
