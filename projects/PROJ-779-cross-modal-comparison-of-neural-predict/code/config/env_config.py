import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from code.utils.logger import get_logger

logger = get_logger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class EnvironmentConfig:
    """
    Manages environment configuration loading from .env files with fallback to defaults.
    Ensures type safety and validation for critical configuration values.
    """

    # Default values for critical configuration
    DEFAULTS: Dict[str, Any] = {
        # Paths
        "PROJECT_ROOT": str(Path(__file__).resolve().parent.parent.parent),
        "DATA_DIR": "data",
        "CODE_DIR": "code",
        "RESULTS_DIR": "data/results",
        "PROCESSED_DIR": "data/processed",
        
        # Logging
        "LOG_LEVEL": "INFO",
        "LOG_FILE": "logs/pipeline.log",
        
        # Data Processing
        "SAMPLING_RATE_THRESHOLD": "500",
        "TRIAL_ODDBALL_MIN": "100",
        "TRIAL_STANDARD_MIN": "300",
        "TIME_WINDOW_START": "-0.2",
        "TIME_WINDOW_END": "0.8",
        
        # Analysis
        "RANDOM_SEED": "42",
        "N_PERMUTATIONS": "1000",
        
        # ICA
        "ICA_MAX_ITER": "200",
        "ICA_METHOD": "picard",
        
        # Source Localization
        "HEAD_MODEL": "icbm152",
        "SOURCE_SPACE_RES": "5",
    }

    def __init__(self, env_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            env_path: Path to .env file. If None, looks in project root.
        """
        self._config: Dict[str, str] = {}
        self._load_environment(env_path)
        self._load_defaults()
        self._validate()

    def _load_environment(self, env_path: Optional[str]) -> None:
        """Load variables from .env file if it exists."""
        if env_path is None:
            # Default to project root .env
            base_path = Path(self.DEFAULTS["PROJECT_ROOT"])
            env_path = str(base_path / ".env")
        
        env_file = Path(env_path)
        
        if env_file.exists():
            logger.info(f"Loading environment from {env_file}")
            load_dotenv(env_file)
            # Update internal dict with os.environ values that are not defaults
            for key in self.DEFAULTS:
                if key in os.environ:
                    self._config[key] = os.environ[key]
        else:
            logger.warning(f".env file not found at {env_file}, using defaults")

    def _load_defaults(self) -> None:
        """Load default values for any missing keys."""
        for key, value in self.DEFAULTS.items():
            if key not in self._config:
                self._config[key] = value
                logger.debug(f"Using default for {key}: {value}")

    def _validate(self) -> None:
        """Validate critical configuration values."""
        # Validate sampling rate threshold is positive integer
        try:
            val = int(self._config["SAMPLING_RATE_THRESHOLD"])
            if val <= 0:
                raise ConfigError("SAMPLING_RATE_THRESHOLD must be positive")
        except ValueError:
            raise ConfigError("SAMPLING_RATE_THRESHOLD must be an integer")

        # Validate trial counts
        try:
            oddball = int(self._config["TRIAL_ODDBALL_MIN"])
            standard = int(self._config["TRIAL_STANDARD_MIN"])
            if oddball <= 0 or standard <= 0:
                raise ConfigError("Trial counts must be positive")
        except ValueError:
            raise ConfigError("Trial counts must be integers")

        # Validate log level
        log_level = self._config["LOG_LEVEL"].upper()
        if log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigError(f"Invalid LOG_LEVEL: {log_level}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found (shouldn't happen due to defaults)
        
        Returns:
            The configuration value as a string
        """
        return self._config.get(key, default)

    def get_int(self, key: str) -> int:
        """Get configuration value as integer."""
        val = self._config.get(key)
        if val is None:
            raise ConfigError(f"Key {key} not found")
        try:
            return int(val)
        except ValueError:
            raise ConfigError(f"Key {key} must be an integer, got: {val}")

    def get_float(self, key: str) -> float:
        """Get configuration value as float."""
        val = self._config.get(key)
        if val is None:
            raise ConfigError(f"Key {key} not found")
        try:
            return float(val)
        except ValueError:
            raise ConfigError(f"Key {key} must be a float, got: {val}")

    def get_bool(self, key: str) -> bool:
        """Get configuration value as boolean."""
        val = self._config.get(key)
        if val is None:
            raise ConfigError(f"Key {key} not found")
        return val.lower() in ["true", "1", "yes", "on"]

    def get_path(self, key: str) -> Path:
        """Get configuration value as Path object."""
        val = self._config.get(key)
        if val is None:
            raise ConfigError(f"Key {key} not found")
        return Path(val)

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()

# Global instance
_config_instance: Optional[EnvironmentConfig] = None

def get_env_config(env_path: Optional[str] = None) -> EnvironmentConfig:
    """
    Get or create the global environment configuration instance.
    
    Args:
        env_path: Optional path to .env file
    
    Returns:
        EnvironmentConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig(env_path)
    return _config_instance

def reload_config(env_path: Optional[str] = None) -> EnvironmentConfig:
    """
    Force reload of configuration (useful for testing).
    
    Args:
        env_path: Optional path to .env file
    
    Returns:
        New EnvironmentConfig instance
    """
    global _config_instance
    _config_instance = EnvironmentConfig(env_path)
    return _config_instance
