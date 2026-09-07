"""
Environment Configuration Management.

Handles loading environment variables from .env files and providing
safe access to configuration values with defaults and validation.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Attempt to import dotenv; if missing, we will fall back to os.environ
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    logging.warning(
        "python-dotenv not installed. .env files will not be loaded automatically. "
        "Install with: pip install python-dotenv"
    )

# Project Root (assuming this file is at code/utils/env_config.py)
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
ENV_FILE_PATH = PROJECT_ROOT / ".env"
EXAMPLE_ENV_PATH = PROJECT_ROOT / "code" / ".env.example"

# Default Paths
DEFAULT_DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DEFAULT_FIGURES_DIR = PROJECT_ROOT / "figures"
DEFAULT_LOGS_DIR = PROJECT_ROOT / "logs"

class EnvConfig:
    """
    Singleton-like manager for environment configuration.
    Loads from .env if available, otherwise uses os.environ.
    """
    _instance: Optional['EnvConfig'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config: Dict[str, str] = {}
        self._load_environment()

    def _load_environment(self):
        """Load environment variables from .env file if it exists."""
        if HAS_DOTENV and ENV_FILE_PATH.exists():
            load_dotenv(dotenv_path=ENV_FILE_PATH)
        
        # Ensure project directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create data and log directories if they don't exist."""
        dirs = [
            self.get_path("DATA_RAW_DIR"),
            self.get_path("DATA_PROCESSED_DIR"),
            self.get_path("DATA_RESULTS_DIR"),
            self.get_path("FIGURES_DIR"),
            self.get_path("LOGS_DIR"),
        ]
        for d in dirs:
            if d and not d.exists():
                d.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get an environment variable value."""
        return os.environ.get(key, default)

    def get_path(self, key: str, default: Optional[Path] = None) -> Path:
        """Get an environment variable as a Path object."""
        val = os.environ.get(key)
        if val:
            return Path(val).resolve()
        if default:
            return default.resolve()
        # Fallback to defaults defined at module level
        mapping = {
            "DATA_RAW_DIR": DEFAULT_DATA_RAW_DIR,
            "DATA_PROCESSED_DIR": DEFAULT_DATA_PROCESSED_DIR,
            "DATA_RESULTS_DIR": DEFAULT_DATA_RESULTS_DIR,
            "FIGURES_DIR": DEFAULT_FIGURES_DIR,
            "LOGS_DIR": DEFAULT_LOGS_DIR,
        }
        if key in mapping:
            return mapping[key]
        raise ValueError(f"Path configuration '{key}' not found and no default defined.")

    def get_api_key(self, key: str, required: bool = False) -> Optional[str]:
        """
        Safely retrieve an API key.
        
        Args:
            key: The environment variable name (e.g., 'HUGGINGFACE_TOKEN')
            required: If True, raise ValueError if not found.
        
        Returns:
            The API key string or None.
        
        Raises:
            ValueError: If required=True and key is missing.
        """
        val = os.environ.get(key)
        if required and not val:
            raise ValueError(f"Required API key '{key}' is not set in environment.")
        return val

    def to_dict(self) -> Dict[str, str]:
        """Return a copy of current environment variables (filtered for safety)."""
        # Filter out sensitive keys if needed, but for now return relevant project keys
        relevant_keys = [
            "DATA_RAW_DIR", "DATA_PROCESSED_DIR", "DATA_RESULTS_DIR", 
            "FIGURES_DIR", "LOGS_DIR", "LOG_LEVEL"
        ]
        return {k: os.environ.get(k, "") for k in relevant_keys}

# Global instance for convenience
_env_config = EnvConfig()

def get_env_config() -> EnvConfig:
    """Get the global environment configuration instance."""
    return _env_config

def get_path(key: str, default: Optional[Path] = None) -> Path:
    """Convenience function to get a path from config."""
    return _env_config.get_path(key, default)

def get_api_key(key: str, required: bool = False) -> Optional[str]:
    """Convenience function to get an API key from config."""
    return _env_config.get_api_key(key, required)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a raw environment variable."""
    return _env_config.get(key, default)