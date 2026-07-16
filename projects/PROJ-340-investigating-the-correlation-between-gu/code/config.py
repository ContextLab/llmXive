"""
Environment configuration management for the Gut Microbiome-Sleep Architecture project.

This module handles loading, validating, and accessing environment variables
to ensure reproducible and secure configuration across different execution environments.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default paths
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "code" / "config.py"

# Configuration keys
REQUIRED_VARS = {
    "PYTHONHASHSEED": "42",  # For deterministic hashing
    "NPY_RNG_SEED": "42",    # For NumPy random state
    "LOG_LEVEL": "INFO",
}

OPTIONAL_VARS = {
    "DATA_SOURCE": "synthetic",  # Options: 'synthetic', 'real', 'local_file'
    "DATA_PATH": str(PROJECT_ROOT / "data" / "raw"),
    "OUTPUT_PATH": str(PROJECT_ROOT / "data" / "results"),
    "FIGURE_PATH": str(PROJECT_ROOT / "figures"),
    "CACHE_PATH": str(PROJECT_ROOT / "data" / "cache"),
    "MAX_WORKERS": "4",
    "TIMEOUT_SECONDS": "21600",  # 6 hours in seconds
}

class Config:
    """
    Configuration manager for the project.
    
    Loads environment variables from .env file or system environment,
    validates required variables, and provides typed access to configuration values.
    """
    
    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize configuration from environment file or system environment.
        
        Args:
            env_file: Path to .env file. Defaults to PROJECT_ROOT/.env
        """
        self.env_file = env_file or DEFAULT_ENV_FILE
        self._config: Dict[str, Any] = {}
        self._load_environment()
        self._validate()
    
    def _load_environment(self) -> None:
        """Load environment variables from .env file if it exists."""
        if self.env_file.exists():
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
    
    def _validate(self) -> None:
        """Validate that all required environment variables are set."""
        missing = []
        for key, default in REQUIRED_VARS.items():
            if key not in os.environ:
                # Set default if not present
                os.environ[key] = default
                missing.append(f"{key} (set to default: {default})")
            else:
                self._config[key] = os.environ[key]
        
        # Add optional variables with defaults
        for key, default in OPTIONAL_VARS.items():
            self._config[key] = os.environ.get(key, default)
            if key not in os.environ:
                os.environ[key] = self._config[key]
        
        if missing:
            print(f"Warning: Missing required variables set to defaults: {', '.join(missing)}")
    
    def get(self, key: str, default: Any = None, cast: type = str) -> Any:
        """
        Get a configuration value with optional type casting.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            cast: Type to cast the value to
        
        Returns:
            Configuration value cast to specified type
        """
        value = self._config.get(key, default)
        if value is None:
            return default
        
        try:
            if cast == bool:
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif cast == int:
                return int(value)
            elif cast == float:
                return float(value)
            elif cast == Path:
                return Path(value)
            else:
                return cast(value)
        except (ValueError, TypeError):
            return default
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get an integer configuration value."""
        return self.get(key, default, int)
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a float configuration value."""
        return self.get(key, default, float)
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get a boolean configuration value."""
        return self.get(key, default, bool)
    
    def get_path(self, key: str, default: Optional[Path] = None) -> Path:
        """Get a Path configuration value."""
        return self.get(key, default, Path)
    
    @property
    def data_source(self) -> str:
        """Get the configured data source."""
        return self.get("DATA_SOURCE", "synthetic")
    
    @property
    def data_path(self) -> Path:
        """Get the configured data path."""
        return self.get_path("DATA_PATH", PROJECT_ROOT / "data" / "raw")
    
    @property
    def output_path(self) -> Path:
        """Get the configured output path."""
        return self.get_path("OUTPUT_PATH", PROJECT_ROOT / "data" / "results")
    
    @property
    def figure_path(self) -> Path:
        """Get the configured figure path."""
        return self.get_path("FIGURE_PATH", PROJECT_ROOT / "figures")
    
    @property
    def cache_path(self) -> Path:
        """Get the configured cache path."""
        return self.get_path("CACHE_PATH", PROJECT_ROOT / "data" / "cache")
    
    @property
    def log_level(self) -> str:
        """Get the configured log level."""
        return self.get("LOG_LEVEL", "INFO")
    
    @property
    def random_seed(self) -> int:
        """Get the random seed for reproducibility."""
        return self.get_int("NPY_RNG_SEED", 42)
    
    @property
    def max_workers(self) -> int:
        """Get the maximum number of worker threads."""
        return self.get_int("MAX_WORKERS", 4)
    
    @property
    def timeout_seconds(self) -> int:
        """Get the timeout in seconds."""
        return self.get_int("TIMEOUT_SECONDS", 21600)
    
    def ensure_paths_exist(self) -> None:
        """Ensure all configured paths exist, creating them if necessary."""
        paths = [self.data_path, self.output_path, self.figure_path, self.cache_path]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        return self._config.copy()
    
    def to_json(self, indent: int = 2) -> str:
        """Return configuration as a JSON string."""
        return json.dumps(self._config, indent=indent, default=str)
    
    def __repr__(self) -> str:
        return f"Config(data_source={self.data_source}, random_seed={self.random_seed})"

# Global config instance
config = Config()

def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: Global configuration object
    """
    return config

def load_config(env_file: Optional[Path] = None) -> Config:
    """
    Load and return a new configuration instance.
    
    Args:
        env_file: Optional path to .env file
    
    Returns:
        Config: Configuration object
    """
    return Config(env_file)
