"""
Environment configuration management for API keys and data paths.

This module provides functionality to:
- Load environment variables from .env files
- Validate required configuration values
- Provide typed access to configuration values
- Setup logging and paths based on configuration
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from .config import Config, ConfigError, get_config, init_config as init_base_config

class EnvConfigError(Exception):
    """Custom exception for environment configuration errors."""
    pass

class EnvConfig:
    """
    Environment configuration manager.

    Handles loading, validation, and access to environment variables
    and configuration files.
    """

    def __init__(self, config: Config):
        self._config = config
        self._env_vars: Dict[str, str] = {}
        self._required_keys: List[str] = [
            'DATA_ROOT',
            'DATA_RAW',
            'DATA_PROCESSED',
            'DATA_RESULTS',
            'CONFIG_ROOT',
            'SCHEMA_PATH',
            'MODEL_STRUCTURE_PATH',
            'LOG_LEVEL',
            'LOG_FILE'
        ]
        self._optional_keys: List[str] = [
            'ZENODO_API_TOKEN',
            'PUSHSHIFT_API_TOKEN',
            'DATA_VALIDATION',
            'DATA_LEXICONS',
            'MAX_RETRIES',
            'BASE_DELAY',
            'MAX_DELAY',
            'RATE_LIMIT_WINDOW',
            'RANDOM_SEED',
            'BOOTSTRAP_ITERATIONS',
            'CONFIDENCE_LEVEL',
            'MIN_MATCH_RATE',
            'MIN_MATCH_COUNT',
            'MAX_RUNTIME_HOURS',
            'MIN_MARGINAL_R2_GAIN'
        ]

    def load_from_file(self, env_file_path: Optional[Path] = None) -> None:
        """
        Load environment variables from a .env file.

        Args:
            env_file_path: Path to the .env file. If None, searches for .env
                           in the project root and current directory.

        Raises:
            EnvConfigError: If the file exists but cannot be parsed.
        """
        if env_file_path is None:
            # Search for .env in common locations
            possible_paths = [
                Path.cwd() / '.env',
                Path.cwd() / 'config' / '.env',
                Path(__file__).parent.parent.parent.parent / '.env'
            ]
            for path in possible_paths:
                if path.exists():
                    env_file_path = path
                    break

        if env_file_path and env_file_path.exists():
            self._parse_env_file(env_file_path)
        else:
            logging.warning("No .env file found. Using system environment variables.")

    def _parse_env_file(self, file_path: Path) -> None:
        """Parse a .env file and populate _env_vars."""
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                if '=' not in line:
                    continue

                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()

                # Remove surrounding quotes if present
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    value = value[1:-1]

                self._env_vars[key] = value

    def _populate_from_system(self) -> None:
        """Populate env_vars from os.environ for keys we care about."""
        for key in self._required_keys + self._optional_keys:
            if key in os.environ:
                self._env_vars[key] = os.environ[key]

    def _expand_env_vars(self, value: str) -> str:
        """Expand ${VAR_NAME} patterns in a string using loaded env vars."""
        import re
        pattern = r'\$\{([^}]+)\}'

        def replacer(match):
            var_name = match.group(1)
            return self._env_vars.get(var_name, match.group(0))

        return re.sub(pattern, replacer, value)

    def validate(self) -> None:
        """
        Validate that all required configuration values are present.

        Raises:
            EnvConfigError: If any required key is missing or empty.
        """
        missing_keys = []
        for key in self._required_keys:
            value = self._env_vars.get(key)
            if not value:
                missing_keys.append(key)

        if missing_keys:
            raise EnvConfigError(
                f"Missing required environment variables: {', '.join(missing_keys)}. "
                f"Please ensure they are set in your .env file or system environment."
            )

    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get an environment variable value.

        Args:
            key: The environment variable name.
            default: Default value if key is not found.

        Returns:
            The value of the environment variable, or default.
        """
        return self._env_vars.get(key, default)

    def get_int(self, key: str, default: Optional[int] = None) -> int:
        """Get an integer environment variable."""
        value = self._env_vars.get(key, default)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            raise EnvConfigError(f"Cannot convert {key}='{value}' to integer")

    def get_float(self, key: str, default: Optional[float] = None) -> float:
        """Get a float environment variable."""
        value = self._env_vars.get(key, default)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            raise EnvConfigError(f"Cannot convert {key}='{value}' to float")

    def get_path(self, key: str) -> Path:
        """Get an environment variable as a Path object."""
        value = self._env_vars.get(key)
        if not value:
            raise EnvConfigError(f"Environment variable {key} is not set")
        expanded = self._expand_env_vars(value)
        return Path(expanded)

    def get_paths(self) -> Dict[str, Path]:
        """Get all configured paths as a dictionary."""
        return {
            'data_root': self.get_path('DATA_ROOT'),
            'data_raw': self.get_path('DATA_RAW'),
            'data_processed': self.get_path('DATA_PROCESSED'),
            'data_results': self.get_path('DATA_RESULTS'),
            'data_validation': self.get_path('DATA_VALIDATION'),
            'data_lexicons': self.get_path('DATA_LEXICONS'),
            'config_root': self.get_path('CONFIG_ROOT'),
            'schema_path': self.get_path('SCHEMA_PATH'),
            'model_structure_path': self.get_path('MODEL_STRUCTURE_PATH'),
            'log_file': self.get_path('LOG_FILE')
        }

    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get all API keys configured."""
        return {
            'zenodo': self.get('ZENODO_API_TOKEN'),
            'pushshift': self.get('PUSHSHIFT_API_TOKEN')
        }

    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration values."""
        return {
            'max_retries': self.get_int('MAX_RETRIES', 5),
            'base_delay': self.get_int('BASE_DELAY', 1),
            'max_delay': self.get_int('MAX_DELAY', 60),
            'rate_limit_window': self.get_int('RATE_LIMIT_WINDOW', 60)
        }

    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration values."""
        return {
            'random_seed': self.get_int('RANDOM_SEED', 42),
            'bootstrap_iterations': self.get_int('BOOTSTRAP_ITERATIONS', 1000),
            'confidence_level': self.get_float('CONFIDENCE_LEVEL', 0.95)
        }

    def get_validation_thresholds(self) -> Dict[str, Any]:
        """Get validation threshold values."""
        return {
            'min_match_rate': self.get_float('MIN_MATCH_RATE', 0.80),
            'min_match_count': self.get_int('MIN_MATCH_COUNT', 500),
            'max_runtime_hours': self.get_int('MAX_RUNTIME_HOURS', 6),
            'min_marginal_r2_gain': self.get_float('MIN_MARGINAL_R2_GAIN', 0.05)
        }

# Global instance
_env_config: Optional[EnvConfig] = None

def init_env_config(config: Optional[Config] = None, env_file_path: Optional[Path] = None) -> EnvConfig:
    """
    Initialize the global environment configuration.

    Args:
        config: Optional Config instance. If None, initializes base config.
        env_file_path: Optional path to .env file.

    Returns:
        The initialized EnvConfig instance.
    """
    global _env_config

    if _env_config is not None:
        return _env_config

    if config is None:
        config = init_base_config()

    _env_config = EnvConfig(config)
    _env_config.load_from_file(env_file_path)
    _env_config._populate_from_system()
    _env_config.validate()

    return _env_config

def get_env_config() -> EnvConfig:
    """
    Get the global environment configuration instance.

    Returns:
        The EnvConfig instance.

    Raises:
        EnvConfigError: If the configuration has not been initialized.
    """
    global _env_config

    if _env_config is None:
        raise EnvConfigError(
            "Environment configuration not initialized. Call init_env_config() first."
        )

    return _env_config

def setup_environment_from_file(env_file_path: Optional[Path] = None) -> None:
    """
    Setup environment by initializing config and loading .env file.

    Args:
        env_file_path: Optional path to .env file.
    """
    init_env_config(env_file_path=env_file_path)

def validate_and_setup_environment(
    env_file_path: Optional[Path] = None,
    create_if_missing: bool = False
) -> None:
    """
    Validate environment configuration and setup if needed.

    Args:
        env_file_path: Optional path to .env file.
        create_if_missing: If True, create a default .env file if missing.

    Raises:
        EnvConfigError: If validation fails and create_if_missing is False.
    """
    try:
        setup_environment_from_file(env_file_path)
    except EnvConfigError as e:
        if create_if_missing:
            env_file = env_file_path or Path.cwd() / '.env'
            if not env_file.exists():
                # Create a default .env file from example
                example_path = Path.cwd() / 'config' / '.env.example'
                if example_path.exists():
                    with open(example_path, 'r') as src:
                        with open(env_file, 'w') as dst:
                            dst.write(src.read())
                    logging.info(f"Created {env_file} from template. Please fill in values.")
                else:
                    raise EnvConfigError(
                        f"No .env.example found at {example_path}. "
                        "Please create a .env file with required variables."
                    )
            # Re-initialize after creating file
            setup_environment_from_file(env_file)
        else:
            raise
