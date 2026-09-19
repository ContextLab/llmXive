"""
Configuration management module for the root architecture prediction pipeline.
Handles environment variable loading, validation, and centralized config access.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from dotenv import load_dotenv

# Constants for default values
DEFAULT_RUN_MODE = "production"
DEFAULT_RANDOM_SEED = 42
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_PERMUTATION_ITERATIONS = 1000

# Valid run modes
VALID_RUN_MODES = {"production", "test"}

# Required environment variables
REQUIRED_ENV_VARS: List[str] = []  # No strictly required vars, all have defaults

# Optional environment variables with defaults
OPTIONAL_ENV_VARS: Dict[str, Any] = {
    "RUN_MODE": DEFAULT_RUN_MODE,
    "RANDOM_SEED": DEFAULT_RANDOM_SEED,
    "LOG_LEVEL": DEFAULT_LOG_LEVEL,
    "PERMUTATION_ITERATIONS": DEFAULT_PERMUTATION_ITERATIONS,
}

logger = logging.getLogger(__name__)


def load_environment(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file. If None, looks for .env in the project root.

    Returns:
        bool: True if loaded successfully, False otherwise.
    """
    if env_path is None:
        # Default to project root .env
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / ".env"

    if not env_path.exists():
        logger.warning(f".env file not found at {env_path}. Using system environment variables.")
        return False

    try:
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"Loaded environment variables from {env_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to load .env file: {e}")
        return False


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable value.

    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.

    Returns:
        The environment variable value or the default.
    """
    return os.getenv(key, default)


def get_config() -> Dict[str, Any]:
    """
    Load and return all configuration values as a dictionary.
    This function ensures environment variables are loaded and validates them.

    Returns:
        Dict containing all configuration values.

    Raises:
        ValueError: If required environment variables are missing or invalid.
    """
    # Ensure environment is loaded
    load_environment()

    config = {}

    # Run Mode
    run_mode = os.getenv("RUN_MODE", DEFAULT_RUN_MODE)
    if run_mode not in VALID_RUN_MODES:
        raise ValueError(f"Invalid RUN_MODE: '{run_mode}'. Must be one of {VALID_RUN_MODES}")
    config["RUN_MODE"] = run_mode

    # Random Seed (integer)
    try:
        random_seed = int(os.getenv("RANDOM_SEED", DEFAULT_RANDOM_SEED))
        config["RANDOM_SEED"] = random_seed
    except ValueError:
        raise ValueError("RANDOM_SEED must be an integer")

    # Log Level
    log_level = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_log_levels:
        raise ValueError(f"Invalid LOG_LEVEL: '{log_level}'. Must be one of {valid_log_levels}")
    config["LOG_LEVEL"] = log_level

    # Permutation Iterations (integer)
    try:
        perm_iterations = int(os.getenv("PERMUTATION_ITERATIONS", DEFAULT_PERMUTATION_ITERATIONS))
        if perm_iterations <= 0:
            raise ValueError("PERMUTATION_ITERATIONS must be positive")
        config["PERMUTATION_ITERATIONS"] = perm_iterations
    except ValueError:
        raise ValueError("PERMUTATION_ITERATIONS must be a positive integer")

    # Optional: SoilGrids API Key
    if os.getenv("SOILGRIDS_API_KEY"):
        config["SOILGRIDS_API_KEY"] = os.getenv("SOILGRIDS_API_KEY")

    # Optional: Max Rows
    max_rows_str = os.getenv("MAX_ROWS")
    if max_rows_str:
        try:
            config["MAX_ROWS"] = int(max_rows_str)
        except ValueError:
            raise ValueError("MAX_ROWS must be an integer")

    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate the configuration dictionary.

    Args:
        config: The configuration dictionary to validate.

    Returns:
        bool: True if valid.

    Raises:
        ValueError: If validation fails.
    """
    # Basic validation is already done in get_config, but this can be extended
    if "RUN_MODE" not in config:
        raise ValueError("RUN_MODE is missing from config")
    if "RANDOM_SEED" not in config:
        raise ValueError("RANDOM_SEED is missing from config")
    return True


class Config:
    """
    Singleton configuration class for easy access to settings throughout the pipeline.
    """
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._config = get_config()
        return cls._instance

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value by key."""
        return self._config.get(key, default)

    def get_run_mode(self) -> str:
        """Get the current run mode."""
        return self._config.get("RUN_MODE", DEFAULT_RUN_MODE)

    def get_random_seed(self) -> int:
        """Get the random seed."""
        return self._config.get("RANDOM_SEED", DEFAULT_RANDOM_SEED)

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.get_run_mode() == "production"

    def is_test(self) -> bool:
        """Check if running in test mode."""
        return self.get_run_mode() == "test"
