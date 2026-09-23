"""
Environment configuration management for API keys and data paths.

This module provides a centralized way to manage environment variables,
API keys, and data paths required for the project. It extends the
existing Config class to handle environment-specific settings.

Usage:
    config = init_config()
    api_key = config.get_api_key('PUSHSHIFT_API_KEY')
    data_path = config.get_data_path('RAW_DATA_DIR')
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from .config import Config, ConfigError, get_config, init_config as init_base_config

# Define required environment variables
REQUIRED_ENV_VARS = [
    'PROJECT_ROOT',
    'DATA_RAW_DIR',
    'DATA_PROCESSED_DIR',
    'DATA_RESULTS_DIR',
    'DATA_VALIDATION_DIR',
    'DATA_LEXICONS_DIR',
    'CONFIG_DIR',
    'LOGS_DIR',
]

OPTIONAL_ENV_VARS = [
    'PUSHSHIFT_API_KEY',
    'ZENODO_API_TOKEN',
    'DEBUG_MODE',
    'LOG_LEVEL',
]

class EnvConfigError(ConfigError):
    """Custom exception for environment configuration errors."""
    pass

class EnvConfig(Config):
    """
    Extended configuration class that handles environment variables
    and provides typed access to configuration values.
    """
    
    def __init__(self, config_dict: Dict[str, Any], base_config: Optional[Config] = None):
        super().__init__(config_dict)
        self._base_config = base_config
        self._logger = logging.getLogger(__name__)
        
    def get_env_var(self, key: str, required: bool = True, default: Optional[str] = None) -> str:
        """
        Get an environment variable with validation.
        
        Args:
            key: Environment variable name
            required: Whether the variable is required
            default: Default value if not required and not set
        
        Returns:
            The environment variable value
        
        Raises:
            EnvConfigError: If required variable is not set
        """
        value = os.environ.get(key)
        
        if value is None:
            if required:
                raise EnvConfigError(f"Required environment variable '{key}' is not set")
            return default
        
        return value
    
    def get_api_key(self, key: str, required: bool = True) -> str:
        """
        Get an API key from environment variables.
        
        Args:
            key: API key environment variable name
            required: Whether the key is required
        
        Returns:
            The API key value
        
        Raises:
            EnvConfigError: If required key is not set
        """
        return self.get_env_var(key, required=required)
    
    def get_data_path(self, key: str, required: bool = True) -> Path:
        """
        Get a data path from environment variables.
        
        Args:
            key: Data path environment variable name
            required: Whether the path is required
        
        Returns:
            Path object for the data directory
        
        Raises:
            EnvConfigError: If required path is not set
        """
        path_str = self.get_env_var(key, required=required)
        if path_str is None:
            return None
        
        path = Path(path_str)
        
        # Ensure the path exists
        if required and not path.exists():
            raise EnvConfigError(f"Required data path '{key}' does not exist: {path}")
        
        return path
    
    def get_project_root(self) -> Path:
        """Get the project root directory."""
        return self.get_data_path('PROJECT_ROOT')
    
    def get_raw_data_dir(self) -> Path:
        """Get the raw data directory."""
        return self.get_data_path('DATA_RAW_DIR')
    
    def get_processed_data_dir(self) -> Path:
        """Get the processed data directory."""
        return self.get_data_path('DATA_PROCESSED_DIR')
    
    def get_results_data_dir(self) -> Path:
        """Get the results data directory."""
        return self.get_data_path('DATA_RESULTS_DIR')
    
    def get_validation_data_dir(self) -> Path:
        """Get the validation data directory."""
        return self.get_data_path('DATA_VALIDATION_DIR')
    
    def get_lexicons_dir(self) -> Path:
        """Get the lexicons directory."""
        return self.get_data_path('DATA_LEXICONS_DIR')
    
    def get_config_dir(self) -> Path:
        """Get the config directory."""
        return self.get_data_path('CONFIG_DIR')
    
    def get_logs_dir(self) -> Path:
        """Get the logs directory."""
        return self.get_data_path('LOGS_DIR')
    
    def get_pushshift_api_key(self) -> str:
        """Get the Pushshift API key."""
        return self.get_api_key('PUSHSHIFT_API_KEY', required=False)
    
    def get_zenodo_api_token(self) -> str:
        """Get the Zenodo API token."""
        return self.get_api_key('ZENODO_API_TOKEN', required=False)
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        debug_str = self.get_env_var('DEBUG_MODE', required=False, default='false')
        return debug_str.lower() in ('true', '1', 'yes')
    
    def get_log_level(self) -> str:
        """Get the log level."""
        return self.get_env_var('LOG_LEVEL', required=False, default='INFO')
    
    def validate_environment(self) -> List[str]:
        """
        Validate that all required environment variables are set.
        
        Returns:
            List of missing required environment variables
        """
        missing = []
        
        for var in REQUIRED_ENV_VARS:
            if var not in os.environ:
                missing.append(var)
        
        return missing
    
    def ensure_directories(self) -> None:
        """
        Ensure all required directories exist.
        
        Raises:
            EnvConfigError: If any directory cannot be created
        """
        dirs = [
            self.get_raw_data_dir(),
            self.get_processed_data_dir(),
            self.get_results_data_dir(),
            self.get_validation_data_dir(),
            self.get_lexicons_dir(),
            self.get_config_dir(),
            self.get_logs_dir(),
        ]
        
        for dir_path in dirs:
            if dir_path and not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self._logger.info(f"Created directory: {dir_path}")
                except OSError as e:
                    raise EnvConfigError(f"Failed to create directory {dir_path}: {e}")

def init_env_config(config_dict: Optional[Dict[str, Any]] = None) -> EnvConfig:
    """
    Initialize environment configuration.
    
    Args:
        config_dict: Optional dictionary with configuration values
        
    Returns:
        EnvConfig instance
    """
    base_config = init_base_config()
    
    if config_dict is None:
        config_dict = {}
    
    # Merge base config with provided config
    merged_config = {**base_config.config_dict, **config_dict}
    
    return EnvConfig(merged_config, base_config)

def get_env_config() -> EnvConfig:
    """
    Get the global environment configuration instance.
    
    Returns:
        EnvConfig instance
    """
    # This assumes init_env_config has been called
    # In a real implementation, you might want to cache the instance
    return init_env_config()

def setup_environment_from_file(config_file: Optional[Path] = None) -> EnvConfig:
    """
    Setup environment variables from a configuration file.
    
    Args:
        config_file: Path to the configuration file (JSON or YAML)
        
    Returns:
        EnvConfig instance
    """
    if config_file is None:
        # Default to config/env_config.json
        config_file = Path('config/env_config.json')
    
    if not config_file.exists():
        # Try to create default config
        _create_default_config(config_file)
    
    with open(config_file, 'r') as f:
        if config_file.suffix == '.yaml':
            import yaml
            config_dict = yaml.safe_load(f)
        else:
            config_dict = json.load(f)
    
    # Set environment variables from config
    for key, value in config_dict.items():
        if isinstance(value, (str, int, float, bool)):
            os.environ[key] = str(value)
        elif isinstance(value, dict):
            for sub_key, sub_value in value.items():
                env_var_name = f"{key}_{sub_key}".upper()
                os.environ[env_var_name] = str(sub_value)
    
    return init_env_config()

def _create_default_config(config_file: Path) -> None:
    """Create a default environment configuration file."""
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        "PROJECT_ROOT": str(Path.cwd()),
        "DATA_RAW_DIR": str(Path.cwd() / "data" / "raw"),
        "DATA_PROCESSED_DIR": str(Path.cwd() / "data" / "processed"),
        "DATA_RESULTS_DIR": str(Path.cwd() / "data" / "results"),
        "DATA_VALIDATION_DIR": str(Path.cwd() / "data" / "validation"),
        "DATA_LEXICONS_DIR": str(Path.cwd() / "data" / "lexicons"),
        "CONFIG_DIR": str(Path.cwd() / "config"),
        "LOGS_DIR": str(Path.cwd() / "logs"),
        "DEBUG_MODE": False,
        "LOG_LEVEL": "INFO",
        # API keys should be set via environment variables or .env file
        # not stored in the config file for security reasons
    }
    
    with open(config_file, 'w') as f:
        json.dump(default_config, f, indent=2)
    
    logging.getLogger(__name__).info(f"Created default config file: {config_file}")

# Convenience function to validate and setup environment
def validate_and_setup_environment() -> EnvConfig:
    """
    Validate environment and ensure directories exist.
    
    Returns:
        EnvConfig instance
    
    Raises:
        EnvConfigError: If validation fails
    """
    config = init_env_config()
    
    missing = config.validate_environment()
    if missing:
        raise EnvConfigError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set them or create a config file at config/env_config.json"
        )
    
    config.ensure_directories()
    
    return config