"""
Environment configuration management for llmXive project.

Loads settings from a .env file with fallback to secure defaults.
Ensures all configuration values are validated before use.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from code.utils.logger import get_logger

logger = get_logger(__name__)

# Default configuration values
DEFAULTS = {
    # Data paths
    "DATA_ROOT": "data",
    "RAW_DATA_DIR": "data/raw",
    "PROCESSED_DATA_DIR": "data/processed",
    "RESULTS_DIR": "data/results",
    "FIGURES_DIR": "figures",
    
    # OpenNeuro dataset identifiers
    "AUDITORY_DATASET_ID": "ds000246",
    "VISUAL_DATASET_ID": "openneuro/ds000117",
    "VISUAL_DATASET_VERSION": "r.0",
    
    # Processing parameters
    "SAMPLING_RATE_THRESHOLD": 500,
    "MIN_ODDBALL_TRIALS": 100,
    "MIN_STANDARD_TRIALS": 300,
    "BANDPASS_LOW": 1.0,
    "BANDPASS_HIGH": 40.0,
    
    # Analysis parameters
    "AUDITORY_WINDOW_START": 0.05,
    "AUDITORY_WINDOW_END": 0.20,
    "VISUAL_WINDOW_START": 0.10,
    "VISUAL_WINDOW_END": 0.30,
    "LATENCY_THRESHOLD_MS": 50,
    "DICE_THRESHOLD": 0.6,
    "TOST_ALPHA": 0.05,
    
    # Reliability parameters
    "SPLIT_HALF_SEED": 42,
    
    # Logging
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "logs/pipeline.log",
    
    # Execution
    "RANDOM_SEED": 42,
    "N_JOBS": 1,
    "MAX_MEMORY_GB": 7,
    "TIMEOUT_HOURS": 6,
}

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class EnvironmentConfig:
    """
    Environment configuration manager.
    
    Loads configuration from .env file or uses defaults.
    Provides type-safe access to configuration values.
    """
    
    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            env_path: Path to .env file. If None, searches in project root.
        """
        self._config: Dict[str, Any] = {}
        self._load_environment(env_path)
        
    def _load_environment(self, env_path: Optional[Path] = None) -> None:
        """
        Load environment variables from .env file.
        
        Args:
            env_path: Path to .env file.
        """
        if env_path is None:
            # Search for .env in project root and parent directories
            current = Path.cwd()
            env_path = current / ".env"
            if not env_path.exists():
                # Try parent directories
                for _ in range(5):
                    current = current.parent
                    env_path = current / ".env"
                    if env_path.exists():
                        break
        
        if env_path.exists():
            logger.info(f"Loading environment from {env_path}")
            load_dotenv(env_path)
        else:
            logger.info("No .env file found, using defaults")
        
        # Load all configuration values
        for key, default in DEFAULTS.items():
            env_value = os.getenv(key)
            if env_value is not None:
                self._config[key] = self._convert_value(env_value, default)
            else:
                self._config[key] = default
        
        logger.debug(f"Configuration loaded: {len(self._config)} values")
    
    def _convert_value(self, value: str, default: Any) -> Any:
        """
        Convert string value to appropriate type based on default.
        
        Args:
            value: String value from environment.
            default: Default value for type inference.
        
        Returns:
            Converted value.
        """
        if isinstance(default, bool):
            return value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(default, int):
            return int(value)
        elif isinstance(default, float):
            return float(value)
        else:
            return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key.
            default: Default value if key not found.
        
        Returns:
            Configuration value.
        """
        if key not in self._config:
            if default is not None:
                return default
            if key in DEFAULTS:
                return DEFAULTS[key]
            raise ConfigError(f"Configuration key '{key}' not found and no default provided")
        return self._config[key]
    
    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """Get integer configuration value."""
        value = self.get(key, default)
        if not isinstance(value, int):
            raise ConfigError(f"Configuration '{key}' must be an integer")
        return value
    
    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """Get float configuration value."""
        value = self.get(key, default)
        if not isinstance(value, (int, float)):
            raise ConfigError(f"Configuration '{key}' must be a number")
        return float(value)
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> bool:
        """Get boolean configuration value."""
        value = self.get(key, default)
        if not isinstance(value, bool):
            raise ConfigError(f"Configuration '{key}' must be a boolean")
        return value
    
    def get_path(self, key: str, default: Optional[Path] = None) -> Path:
        """Get path configuration value."""
        value = self.get(key, default)
        if isinstance(value, Path):
            return value
        return Path(value)
    
    def get_dict(self) -> Dict[str, Any]:
        """Get all configuration as dictionary."""
        return self._config.copy()
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ConfigError: If any configuration value is invalid.
        """
        # Validate sampling rate threshold
        if self.get_int("SAMPLING_RATE_THRESHOLD") < 100:
            raise ConfigError("SAMPLING_RATE_THRESHOLD must be >= 100")
        
        # Validate trial counts
        if self.get_int("MIN_ODDBALL_TRIALS") < 10:
            raise ConfigError("MIN_ODDBALL_TRIALS must be >= 10")
        if self.get_int("MIN_STANDARD_TRIALS") < 10:
            raise ConfigError("MIN_STANDARD_TRIALS must be >= 10")
        
        # Validate time windows
        if self.get_float("AUDITORY_WINDOW_START") >= self.get_float("AUDITORY_WINDOW_END"):
            raise ConfigError("AUDITORY_WINDOW_START must be < AUDITORY_WINDOW_END")
        if self.get_float("VISUAL_WINDOW_START") >= self.get_float("VISUAL_WINDOW_END"):
            raise ConfigError("VISUAL_WINDOW_START must be < VISUAL_WINDOW_END")
        
        # Validate thresholds
        if self.get_float("DICE_THRESHOLD") < 0.0 or self.get_float("DICE_THRESHOLD") > 1.0:
            raise ConfigError("DICE_THRESHOLD must be between 0.0 and 1.0")
        if self.get_float("TOST_ALPHA") <= 0.0 or self.get_float("TOST_ALPHA") >= 1.0:
            raise ConfigError("TOST_ALPHA must be between 0.0 and 1.0")
        
        logger.info("Configuration validation passed")

# Global configuration instance
_config_instance: Optional[EnvironmentConfig] = None

def get_env_config(env_path: Optional[Path] = None) -> EnvironmentConfig:
    """
    Get or create the global configuration instance.
    
    Args:
        env_path: Optional path to .env file.
    
    Returns:
        EnvironmentConfig instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig(env_path)
        _config_instance.validate()
    return _config_instance

def reload_config(env_path: Optional[Path] = None) -> EnvironmentConfig:
    """
    Reload configuration from .env file.
    
    Args:
        env_path: Optional path to .env file.
    
    Returns:
        New EnvironmentConfig instance.
    """
    global _config_instance
    _config_instance = EnvironmentConfig(env_path)
    _config_instance.validate()
    return _config_instance
