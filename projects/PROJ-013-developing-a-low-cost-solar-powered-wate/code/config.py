"""
Configuration management for the solar purification project.
Handles loading of API keys (e.g., NASA POWER) and simulation parameters
from environment variables and a local .env file.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Try to import dotenv; if not installed, provide a graceful fallback
try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    load_dotenv = lambda path=None: None  # type: ignore

from utils import get_project_root, ProjectError, setup_logging

# Initialize logger
logger = setup_logging(__name__)

# Default path for .env file relative to project root
ENV_FILE_PATH = ".env"

# Default configuration values (fallbacks if env vars are missing)
DEFAULT_CONFIG = {
    "NASA_POWER_API_KEY": None,
    "NASA_POWER_BASE_URL": "https://power.larc.nasa.gov/api",
    "SIMULATION_TIME_HOURS": 24,
    "SIMULATION_STEP_SECONDS": 3600,
    "DEFAULT_LATITUDE": 0.0,
    "DEFAULT_LONGITUDE": 0.0,
    "OUTPUT_PRECISION": 4,
}

class Config:
    """
    Centralized configuration manager.
    Loads values from environment variables (precedence) and .env file.
    """

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize configuration.
        
        Args:
            env_path: Optional path to .env file. Defaults to project root/.env
        """
        if env_path is None:
            env_path = get_project_root() / ENV_FILE_PATH
        
        self.env_path = env_path
        self._values: Dict[str, Any] = {}
        
        # Load environment variables from .env file if it exists
        self._load_env_file()
        
        # Load configuration from environment variables (overrides .env)
        self._load_from_env()

    def _load_env_file(self) -> None:
        """Load variables from the .env file if it exists."""
        if not self.env_path.exists():
            logger.debug(f"Environment file not found at {self.env_path}. Skipping.")
            return

        if not HAS_DOTENV:
            logger.warning(
                "python-dotenv is not installed. "
                "Please install it (pip install python-dotenv) to load .env files. "
                "Please set environment variables manually."
            )
            return

        try:
            load_dotenv(self.env_path)
            logger.info(f"Loaded environment variables from {self.env_path}")
        except Exception as e:
            logger.warning(f"Failed to load .env file: {e}")

    def _load_from_env(self) -> None:
        """Load configuration from os.environ, falling back to defaults."""
        for key, default in DEFAULT_CONFIG.items():
            env_val = os.environ.get(key)
            if env_val is not None:
                # Attempt to convert to appropriate type
                if isinstance(default, int):
                    try:
                        self._values[key] = int(env_val)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {key}: {env_val}. Using default.")
                        self._values[key] = default
                elif isinstance(default, float):
                    try:
                        self._values[key] = float(env_val)
                    except ValueError:
                        logger.warning(f"Invalid float value for {key}: {env_val}. Using default.")
                        self._values[key] = default
                elif isinstance(default, bool):
                    self._values[key] = env_val.lower() in ('true', '1', 'yes')
                else:
                    self._values[key] = env_val
            else:
                self._values[key] = default

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value.
        
        Args:
            key: The configuration key.
            default: Default value if key is not found (overrides class defaults).
        
        Returns:
            The configuration value.
        """
        if key in self._values:
            return self._values[key]
        return default

    def get_required(self, key: str) -> str:
        """
        Retrieve a required configuration value.
        
        Args:
            key: The configuration key.
        
        Returns:
            The configuration value.
        
        Raises:
            ProjectError: If the required key is missing or None.
        """
        value = self.get(key)
        if value is None:
            raise ProjectError(f"Required configuration '{key}' is missing. "
                             f"Please set it in your .env file or environment variables.")
        return value

    @property
    def nasa_power_api_key(self) -> Optional[str]:
        """Get the NASA POWER API key."""
        return self.get("NASA_POWER_API_KEY")

    @property
    def nasa_power_base_url(self) -> str:
        """Get the NASA POWER API base URL."""
        return self.get("NASA_POWER_BASE_URL", DEFAULT_CONFIG["NASA_POWER_BASE_URL"])

    @property
    def simulation_time_hours(self) -> int:
        """Get the simulation duration in hours."""
        return self.get("SIMULATION_TIME_HOURS", DEFAULT_CONFIG["SIMULATION_TIME_HOURS"])

    @property
    def simulation_step_seconds(self) -> int:
        """Get the simulation time step in seconds."""
        return self.get("SIMULATION_STEP_SECONDS", DEFAULT_CONFIG["SIMULATION_STEP_SECONDS"])

    @property
    def default_latitude(self) -> float:
        """Get the default latitude."""
        return self.get("DEFAULT_LATITUDE", DEFAULT_CONFIG["DEFAULT_LATITUDE"])

    @property
    def default_longitude(self) -> float:
        """Get the default longitude."""
        return self.get("DEFAULT_LONGITUDE", DEFAULT_CONFIG["DEFAULT_LONGITUDE"])

    @property
    def output_precision(self) -> int:
        """Get the output precision for floating point numbers."""
        return self.get("OUTPUT_PRECISION", DEFAULT_CONFIG["OUTPUT_PRECISION"])

    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._values.copy()

# Global configuration instance
_config_instance: Optional[Config] = None

def get_config(env_path: Optional[Path] = None) -> Config:
    """
    Get the global configuration instance.
    
    Args:
        env_path: Optional path to .env file.
    
    Returns:
        The global Config instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(env_path)
    return _config_instance

def reload_config(env_path: Optional[Path] = None) -> Config:
    """
    Force reload the global configuration.
    
    Args:
        env_path: Optional path to .env file.
    
    Returns:
        The reloaded Config instance.
    """
    global _config_instance
    _config_instance = Config(env_path)
    return _config_instance
