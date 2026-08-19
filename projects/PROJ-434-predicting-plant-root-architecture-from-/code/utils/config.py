"""
Environment configuration management for the plant root architecture pipeline.

Handles loading of .env files, providing typed access to environment variables,
and managing configuration for API keys and paths.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Attempt to import dotenv, but make it optional for environments where it might not be installed
try:
    from dotenv import load_dotenv as _load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    _load_dotenv = None

logger = logging.getLogger(__name__)

class Config:
    """
    Centralized configuration manager.
    
    Loads environment variables from a .env file if present, and provides
    a structured interface for accessing configuration values.
    """
    
    _instance: Optional['Config'] = None
    _initialized: bool = False

    def __new__(cls) -> 'Config':
        """Singleton pattern to ensure single configuration instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._config: Dict[str, Any] = {}
            self._load_config()
            self._initialized = True

    def _load_config(self) -> None:
        """
        Load configuration from .env file and environment variables.
        
        Priority:
        1. .env file (if exists)
        2. System environment variables
        """
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / ".env"

        if env_path.exists():
            if HAS_DOTENV:
                _load_dotenv(dotenv_path=env_path, override=True)
                logger.info(f"Loaded environment variables from {env_path}")
            else:
                logger.warning(
                    "python-dotenv not installed. .env file found but not loaded. "
                    "Install with: pip install python-dotenv"
                )
        else:
            logger.debug(f"No .env file found at {env_path}")

        # Store relevant environment variables
        self._config = {
            "ROOT_DIR": os.getenv("ROOT_DIR", str(project_root)),
            "DATA_DIR": os.getenv("DATA_DIR", str(project_root / "data")),
            "CODE_DIR": os.getenv("CODE_DIR", str(project_root / "code")),
            "FIGURES_DIR": os.getenv("FIGURES_DIR", str(project_root / "figures")),
            "ARTIFACTS_DIR": os.getenv("ARTIFACTS_DIR", str(project_root / "artifacts")),
            "LOGS_DIR": os.getenv("LOGS_DIR", str(project_root / "data" / "logs")),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        }

        # API Keys (optional, only set if present in env)
        api_keys = ["API_KEY", "SOILGRID_API_KEY", "ZENODO_API_TOKEN"]
        for key in api_keys:
            value = os.getenv(key)
            if value:
                self._config[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
        
        Returns:
            The configuration value or default
        """
        return self._config.get(key, default)

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a raw environment variable.
        
        Args:
            key: Environment variable name
            default: Default value if not found
        
        Returns:
            The environment variable value or default
        """
        return os.getenv(key, default)

    def require(self, key: str) -> str:
        """
        Get a required configuration value, raising an error if missing.
        
        Args:
            key: Configuration key
        
        Returns:
            The configuration value
        
        Raises:
            KeyError: If the key is not found
        """
        if key not in self._config:
            raise KeyError(f"Required configuration key '{key}' not found. "
                           f"Please set it in .env or environment variables.")
        return self._config[key]

    @property
    def root_dir(self) -> Path:
        return Path(self._config["ROOT_DIR"])

    @property
    def data_dir(self) -> Path:
        return Path(self._config["DATA_DIR"])

    @property
    def code_dir(self) -> Path:
        return Path(self._config["CODE_DIR"])

    @property
    def figures_dir(self) -> Path:
        return Path(self._config["FIGURES_DIR"])

    @property
    def artifacts_dir(self) -> Path:
        return Path(self._config["ARTIFACTS_DIR"])

    @property
    def logs_dir(self) -> Path:
        return Path(self._config["LOGS_DIR"])

    @property
    def random_seed(self) -> int:
        return self._config["RANDOM_SEED"]

    @property
    def log_level(self) -> str:
        return self._config["LOG_LEVEL"]


def load_environment(env_path: Optional[Path] = None) -> None:
    """
    Load environment variables from a .env file.
    
    This function is a convenience wrapper that can be called explicitly
    to load a .env file before initializing the Config singleton.
    
    Args:
        env_path: Path to the .env file. If None, searches for .env 
                 in the project root.
    """
    if not HAS_DOTENV:
        logger.warning("python-dotenv not installed. Cannot load .env file.")
        return

    if env_path is None:
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / ".env"

    if env_path.exists():
        _load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.debug(f"No .env file found at {env_path}")


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a raw environment variable value.
    
    Args:
        key: Environment variable name
        default: Default value if not found
    
    Returns:
        The environment variable value or default
    """
    return os.getenv(key, default)


# Convenience function to get the singleton config instance
def get_config() -> Config:
    """
    Get the singleton Config instance.
    
    Returns:
        The Config instance
    """
    return Config()
