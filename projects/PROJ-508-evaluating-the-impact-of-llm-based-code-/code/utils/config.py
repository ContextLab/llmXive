"""
Configuration management module.
Handles environment variables and API key loading.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

class Config:
    """Configuration holder for the project."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._load_env()
        self._load_defaults()

    def _load_env(self) -> None:
        """Load configuration from environment variables."""
        self._data["github_api_base"] = os.getenv(
            "GITHUB_API_BASE", 
            "https://api.github.com"
        )
        self._data["github_token"] = os.getenv("GITHUB_TOKEN", "")
        self._data["log_level"] = os.getenv("LOG_LEVEL", "INFO")

    def _load_defaults(self) -> None:
        """Set default values if not present."""
        if "data_dir" not in self._data:
            self._data["data_dir"] = str(Path(__file__).parent.parent.parent / "data")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Return the configuration as a dictionary."""
        return self._data.copy()


_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the singleton configuration instance.
    
    Returns:
        The global Config instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
