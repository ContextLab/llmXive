"""
Environment configuration management for the Qwen-VLA Cross-Embodiment Transfer Study.

Handles .env loading, default path resolution, and configuration validation.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Try to import dotenv, but handle missing gracefully if not installed
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logging.warning("python-dotenv not installed. Environment variables will only be read from the system.")

# Project root relative to this file (src/utils/config.py -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Default paths relative to project root
DEFAULTS = {
    "DATA_DIR": "data",
    "CHECKPOINTS_DIR": "data/checkpoints",
    "LOGS_DIR": "data/logs",
    "FIGURES_DIR": "figures",
    "MODEL_CACHE_DIR": "data/cache",
    "ENV_FILE": ".env",
    "METADATA_FILE": "data/metadata.yaml",
    "MANIFEST_FILE": "data/manifest.yaml",
    "SEEDS_FILE": "data/seeds.json",
    "RESULTS_DIR": "data/results",
}

class Config:
    """
    Centralized configuration manager.
    Loads environment variables from .env (if present) and system environment.
    Provides typed access to configuration values.
    """

    _instance: Optional['Config'] = None
    _initialized: bool = False

    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._config: Dict[str, Any] = {}
        self._logger = logging.getLogger(__name__)
        self._load_environment()
        self._init_paths()
        self._initialized = True

    def _load_environment(self) -> None:
        """Load .env file if available, then merge with system environment."""
        env_path = _PROJECT_ROOT / self.get("ENV_FILE", DEFAULTS["ENV_FILE"])
        
        if DOTENV_AVAILABLE:
            if env_path.exists():
                load_dotenv(env_path)
                self._logger.info(f"Loaded environment from {env_path}")
            else:
                self._logger.debug(f"No .env file found at {env_path}, using system environment")
        else:
            if env_path.exists():
                self._logger.warning(
                    f"Environment file {env_path} exists but python-dotenv is not installed. "
                    "Variables will not be loaded automatically."
                )

        # Populate config from os.environ
        for key in DEFAULTS.keys():
            env_val = os.environ.get(key)
            if env_val is not None:
                self._config[key] = env_val

    def _init_paths(self) -> None:
        """Ensure required directories exist."""
        path_keys = [
            "DATA_DIR", "CHECKPOINTS_DIR", "LOGS_DIR", 
            "FIGURES_DIR", "MODEL_CACHE_DIR", "RESULTS_DIR"
        ]
        
        for key in path_keys:
            base_path = self.get(key)
            full_path = _PROJECT_ROOT / base_path
            full_path.mkdir(parents=True, exist_ok=True)
            self._config[f"{key}_PATH"] = full_path

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (e.g., 'DATA_DIR')
            default: Default value if key not found
        
        Returns:
            The configuration value or default
        """
        return self._config.get(key, default)

    def get_path(self, key: str, relative_to: Optional[Path] = None) -> Path:
        """
        Get a configuration value as a Path object.
        
        Args:
            key: Configuration key (e.g., 'CHECKPOINTS_DIR')
            relative_to: Base path to resolve against (defaults to PROJECT_ROOT)
        
        Returns:
            Resolved Path object
        """
        base = relative_to or _PROJECT_ROOT
        val = self.get(key)
        if val is None:
            return base
        return base / val

    @property
    def project_root(self) -> Path:
        """Return the project root path."""
        return _PROJECT_ROOT

    @property
    def data_dir(self) -> Path:
        """Return the data directory path."""
        return self.get_path("DATA_DIR")

    @property
    def checkpoints_dir(self) -> Path:
        """Return the checkpoints directory path."""
        return self.get_path("CHECKPOINTS_DIR")

    @property
    def logs_dir(self) -> Path:
        """Return the logs directory path."""
        return self.get_path("LOGS_DIR")

    @property
    def figures_dir(self) -> Path:
        """Return the figures directory path."""
        return self.get_path("FIGURES_DIR")

    @property
    def model_cache_dir(self) -> Path:
        """Return the model cache directory path."""
        return self.get_path("MODEL_CACHE_DIR")

    @property
    def metadata_file(self) -> Path:
        """Return the metadata file path."""
        return self.get_path("METADATA_FILE")

    @property
    def manifest_file(self) -> Path:
        """Return the manifest file path."""
        return self.get_path("MANIFEST_FILE")

    @property
    def seeds_file(self) -> Path:
        """Return the seeds file path."""
        return self.get_path("SEEDS_FILE")

    @property
    def results_dir(self) -> Path:
        """Return the results directory path."""
        return self.get_path("RESULTS_DIR")

    def to_dict(self) -> Dict[str, Any]:
        """Return a dictionary copy of the configuration."""
        return self._config.copy()


# Global config instance
config = Config()


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        The global Config instance
    """
    return config
