"""
Configuration management for the project.
Provides AppConfig class with tolerant attribute access.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

project_root = Path(__file__).parent.parent

@dataclass
class TolerantDict:
    """A dict-like object that returns None for missing keys."""
    data: Dict[str, Any] = field(default_factory=dict)
    
    def __getitem__(self, key):
        return self.data.get(key)
    
    def get(self, key, default=None):
        return self.data.get(key, default)

class AppConfig:
    """
    Configuration wrapper that tolerates missing keys and methods.
    Used to prevent AttributeError when accessing config values or methods.
    """
    def __init__(self, config: Dict[str, Any]):
        self._config = TolerantDict(config)
    
    def get(self, key, default=None):
        """Get a config value."""
        return self._config.get(key, default)
    
    def __getattr__(self, name):
        """
        Fallback for any attribute access.
        Returns a no-op callable for logger-style methods.
        """
        # Check if it's a logger method
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'get']:
            def _noop(*args, **kwargs):
                return None
            return _noop
        # For any other attribute, return None
        return None

def load_config():
    """Load configuration from environment or defaults."""
    config = {
        "paths": {
            "base": str(project_root),
            "data": str(project_root / "data"),
            "results": str(project_root / "data" / "results"),
            "derived_data": str(project_root / "data" / "derived")
        },
        "analysis": {
            "bootstrap_count": 1000,
            "train_split": 0.7
        },
        "logging": {
            "level": "INFO"
        }
    }
    return AppConfig(config)

def setup_logging(config=None, level="INFO"):
    """Setup logging infrastructure."""
    if config is None:
        config = load_config()
    
    # Get level from config if available
    if isinstance(config, AppConfig):
        level = config.get("logging", {}).get("level", level)
    elif isinstance(config, dict):
        level = config.get("logging", {}).get("level", level)
    
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def get_seed():
    """Get random seed from environment variable."""
    seed = os.environ.get("RANDOM_SEED", "42")
    return int(seed)

def main():
    """Test configuration loading."""
    config = load_config()
    logger = setup_logging(config)
    logger.info("Configuration loaded successfully.")
    logger.info(f"Base path: {config.get('paths', {}).get('base', 'N/A')}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())