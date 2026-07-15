"""
Environment configuration management for the llmXive research pipeline.

This module handles loading configuration from a .env file, setting up
default values for seeds, paths, and logging, and providing a central
configuration object.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Try to import dotenv, but handle gracefully if not present
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = lambda: None

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"

# Default configuration values
DEFAULTS: Dict[str, Any] = {
    "SEED": 42,
    "DATA_RAW_DIR": "data/raw",
    "DATA_PROCESSED_DIR": "data/processed",
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "logs/pipeline.log",
    "LATTICE_SIZES": "16,24",
    "TEMPERATURE_RANGE": "0.1,3.0",
    "NUM_SAMPLES": 1000,
    "BATCH_SIZE": 64,
}

class Config:
    """Central configuration object loaded from environment variables and .env file."""
    
    def __init__(self, env_path: Optional[Path] = None):
        self.env_path = env_path or DEFAULT_ENV_PATH
        self._config: Dict[str, Any] = {}
        self._load_environment()
        self._load_defaults()
        self._setup_logging()

    def _load_environment(self) -> None:
        """Load variables from .env file if it exists."""
        if self.env_path.exists():
            load_dotenv(self.env_path)
        else:
            # Create a sample .env file if it doesn't exist for user convenience
            self._create_sample_env()

    def _create_sample_env(self) -> None:
        """Create a sample .env file with default values."""
        sample_content = """# llmXive Research Pipeline Configuration
# Copy this file to .env and modify values as needed

# Random seed for reproducibility
SEED=42

# Data directories (relative to project root)
DATA_RAW_DIR=data/raw
DATA_PROCESSED_DIR=data/processed

# Logging configuration
LOG_LEVEL=INFO
LOG_FILE=logs/pipeline.log

# Simulation parameters
LATTICE_SIZES=16,24
TEMPERATURE_RANGE=0.1,3.0
NUM_SAMPLES=1000
BATCH_SIZE=64
"""
        # Ensure logs directory exists
        (PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)
        with open(self.env_path, "w") as f:
            f.write(sample_content)

    def _load_defaults(self) -> None:
        """Load configuration from environment variables or defaults."""
        for key, default_value in DEFAULTS.items():
            env_value = os.getenv(key)
            if env_value is not None:
                # Try to parse the value appropriately
                if isinstance(default_value, int):
                    try:
                        self._config[key] = int(env_value)
                    except ValueError:
                        self._config[key] = default_value
                elif isinstance(default_value, float):
                    try:
                        self._config[key] = float(env_value)
                    except ValueError:
                        self._config[key] = default_value
                elif isinstance(default_value, list):
                    # Parse comma-separated string to list
                    self._config[key] = [item.strip() for item in env_value.split(",")]
                else:
                    self._config[key] = env_value
            else:
                self._config[key] = default_value

    def _setup_logging(self) -> None:
        """Configure logging based on configuration."""
        log_level = getattr(logging, str(self._config["LOG_LEVEL"]).upper(), logging.INFO)
        log_file = PROJECT_ROOT / self._config["LOG_FILE"]
        
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        """Get a configuration value as integer."""
        value = self._config.get(key, default)
        return int(value)

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Get a configuration value as float."""
        value = self._config.get(key, default)
        return float(value)

    def get_list(self, key: str, default: Optional[list] = None) -> list:
        """Get a configuration value as list."""
        value = self._config.get(key, default)
        if isinstance(value, str):
            return [item.strip() for item in value.split(",")]
        return value if value is not None else []

    def get_path(self, key: str) -> Path:
        """Get a configuration value as Path, resolved relative to project root."""
        value = self._config.get(key)
        if value is None:
            raise KeyError(f"Configuration key '{key}' not found")
        return PROJECT_ROOT / value

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()

    def __repr__(self) -> str:
        return f"Config({self._config})"


# Global config instance
config: Optional[Config] = None

def get_config(env_path: Optional[Path] = None) -> Config:
    """Get or create the global configuration instance."""
    global config
    if config is None:
        config = Config(env_path)
    return config

def reset_config() -> None:
    """Reset the global configuration instance (useful for testing)."""
    global config
    config = None