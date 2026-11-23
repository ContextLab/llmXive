import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging
from dotenv import load_dotenv

# Load .env from project root if it exists
# We assume this module is imported early in the pipeline
_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

class EnvConfig:
    """
    Centralized environment variable manager.
    Provides type-safe access to configuration values.
    """
    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def get_path(self, key: str, default: Optional[str] = None) -> Optional[Path]:
        """
        Retrieves a path variable from the environment.
        Returns a Path object or None.
        """
        val = os.getenv(key, default)
        if val is None:
            self._logger.warning(f"Environment variable {key} not set.")
            return None
        return Path(val).resolve()

    def get_api_key(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves an API key.
        """
        val = os.getenv(key, default)
        if val is None:
            self._logger.warning(f"API Key {key} not set.")
        return val

    def get_env_var(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Generic environment variable getter.
        """
        return os.getenv(key, default)

_env_config_instance: Optional[EnvConfig] = None

def get_env_config() -> EnvConfig:
    """
    Singleton accessor for EnvConfig.
    """
    global _env_config_instance
    if _env_config_instance is None:
        _env_config_instance = EnvConfig()
    return _env_config_instance

def get_path(key: str, default: Optional[str] = None) -> Optional[Path]:
    """
    Convenience function to get a path.
    """
    return get_env_config().get_path(key, default)

def get_api_key(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get an API key.
    """
    return get_env_config().get_api_key(key, default)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a generic env var.
    """
    return get_env_config().get_env_var(key, default)