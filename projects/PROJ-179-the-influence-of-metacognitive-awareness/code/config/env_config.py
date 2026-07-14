"""
Configuration management for the metacognitive awareness project.

Provides configuration loading, environment variable handling, and
a tolerant configuration access pattern for various callers.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TolerantDict:
    """A dictionary-like class that tolerates missing keys gracefully."""
    _data: Dict[str, Any] = field(default_factory=dict)
    
    def __getitem__(self, key):
        return self._data.get(key)
    
    def __getattr__(self, key):
        return self._data.get(key)
    
    def get(self, key, default=None):
        return self._data.get(key, default)

class AppConfig:
    """Application configuration with tolerant access patterns."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with nested key support."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def __getattr__(self, name: str) -> Any:
        """Allow attribute-style access to config values."""
        if name.startswith('_'):
            raise AttributeError(name)
        return self._data.get(name) if hasattr(self, '_data') else None
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access to config values."""
        return self._config.get(key)

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        # Default paths to try
        possible_paths = [
            Path(__file__).parent / "env_config.yaml",
            Path(__file__).parent.parent / "config" / "env_config.yaml",
            Path.cwd() / "config" / "env_config.yaml"
        ]
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break
        else:
            logger.warning("No config file found, using defaults")
            return {}
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config if config else {}
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        return {}

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    # Handle different input types gracefully
    if isinstance(level, str):
        level = level.upper()
    else:
        level = "INFO"
    
    numeric_level = getattr(logging, level, None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_seed(seed_name: str = "default") -> int:
    """Get random seed from environment or config."""
    env_var = f"RANDOM_SEED_{seed_name.upper()}"
    seed = os.getenv(env_var)
    if seed:
        try:
            return int(seed)
        except ValueError:
            pass
    
    # Try config
    config = load_config()
    seed_val = config.get('random_seeds', {}).get(seed_name, 42)
    return seed_val

def main():
    """Main function for testing."""
    config = load_config()
    logger.info(f"Loaded config: {config}")
    
    app_config = AppConfig(config)
    logger.info(f"Config paths.base: {app_config.get('paths.base', 'default')}")
    
    logger.info("Configuration module loaded successfully")

if __name__ == "__main__":
    main()
