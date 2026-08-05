"""
Environment Configuration Management for llmXive Project.

This module handles loading configuration from a .env file with fallback to
secure defaults. It enforces strict separation between environment-specific
variables and hardcoded project constants.

All sensitive or environment-specific paths (e.g., OpenNeuro cache directories,
output paths) should be defined here.

Note: This implementation strictly adheres to the "Real Data" principle.
No synthetic data generation flags are exposed or permitted.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from code.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class EnvironmentConfig:
    """
    Container for environment-based configuration values.

    Loads from .env file if present, otherwise uses safe defaults.
    """

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            env_path: Path to .env file. If None, searches in project root.
        """
        self._config: Dict[str, Any] = {}
        self._load_env(env_path)
        self._validate()

    def _load_env(self, env_path: Optional[Path]) -> None:
        """Load environment variables from .env file."""
        if env_path is None:
            # Default to project root .env
            env_path = Path(__file__).parent.parent.parent / ".env"

        if env_path.exists():
            logger.info(f"Loading environment configuration from {env_path}")
            load_dotenv(env_path)
        else:
            logger.warning(f".env file not found at {env_path}. Using defaults.")

        # Map environment variables to config keys
        # All paths are relative to project root unless absolute is provided
        project_root = Path(__file__).parent.parent.parent

        self._config = {
            # Data Paths
            "RAW_DATA_DIR": os.getenv(
                "RAW_DATA_DIR",
                str(project_root / "data" / "raw")
            ),
            "PROCESSED_DATA_DIR": os.getenv(
                "PROCESSED_DATA_DIR",
                str(project_root / "data" / "processed")
            ),
            "RESULTS_DIR": os.getenv(
                "RESULTS_DIR",
                str(project_root / "data" / "results")
            ),
            "FIGURES_DIR": os.getenv(
                "FIGURES_DIR",
                str(project_root / "figures")
            ),

            # OpenNeuro / External Data Settings
            "OPENNEURO_CACHE_DIR": os.getenv(
                "OPENNEURO_CACHE_DIR",
                str(project_root / "data" / "cache" / "openneuro")
            ),
            "HF_DATASETS_CACHE": os.getenv(
                "HF_DATASETS_CACHE",
                str(project_root / "data" / "cache" / "huggingface")
            ),

            # Processing Parameters (can be overridden via env)
            "SAMPLING_RATE_THRESHOLD": int(
                os.getenv("SAMPLING_RATE_THRESHOLD", "500")
            ),
            "MIN_ODDBALL_TRIALS": int(
                os.getenv("MIN_ODDBALL_TRIALS", "100")
            ),
            "MIN_STANDARD_TRIALS": int(
                os.getenv("MIN_STANDARD_TRIALS", "300")
            ),

            # Logging
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "LOG_FILE": os.getenv(
                "LOG_FILE",
                str(project_root / "logs" / "pipeline.log")
            ),

            # Random Seed
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),

            # Critical: Real Data Enforcement
            # This flag is strictly for documentation/audit purposes.
            # The code logic must NEVER generate synthetic data if this is True.
            "REAL_DATA_ONLY": os.getenv("REAL_DATA_ONLY", "true").lower() in ("true", "1", "yes"),
        }

    def _validate(self) -> None:
        """Validate configuration values."""
        # Ensure directories exist
        for key, path_str in self._config.items():
            if key.endswith("_DIR") or key.endswith("_FILE"):
                path = Path(path_str)
                if not path.parent.exists() and key != "LOG_FILE":
                    # Don't fail on log file parent if logging isn't set up yet
                    pass
                # We do not auto-create directories here to avoid side effects
                # during config loading. Ensure_directories() in config.py handles that.

        # Validate numeric thresholds
        if self._config["SAMPLING_RATE_THRESHOLD"] < 100:
            raise ConfigError("SAMPLING_RATE_THRESHOLD must be >= 100 Hz")

        if self._config["MIN_ODDBALL_TRIALS"] < 10:
            raise ConfigError("MIN_ODDBALL_TRIALS must be >= 10")

        if self._config["MIN_STANDARD_TRIALS"] < 10:
            raise ConfigError("MIN_STANDARD_TRIALS must be >= 10")

        # Validate Real Data Only flag
        if not self._config["REAL_DATA_ONLY"]:
            logger.warning("REAL_DATA_ONLY is False. This violates project constitution.")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return self._config.copy()

    def __repr__(self) -> str:
        return f"EnvironmentConfig({self._config})"


# Singleton instance
_config_instance: Optional[EnvironmentConfig] = None


def get_env_config(env_path: Optional[Path] = None) -> EnvironmentConfig:
    """
    Get the singleton environment configuration instance.

    Args:
        env_path: Optional path to .env file to override default search.

    Returns:
        EnvironmentConfig instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig(env_path)
    return _config_instance


def reload_config(env_path: Optional[Path] = None) -> EnvironmentConfig:
    """
    Force reload of the environment configuration.

    Useful for testing or dynamic reconfiguration.

    Args:
        env_path: Optional path to .env file.

    Returns:
        New EnvironmentConfig instance.
    """
    global _config_instance
    _config_instance = EnvironmentConfig(env_path)
    return _config_instance
