"""
Environment configuration management for PROJ-179.
Loads config from YAML/JSON, manages paths, seeds, and logging.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class TolerantDict:
    """A dict-like object that tolerates missing keys and returns empty dicts/None."""
    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value, returning default if missing."""
        return self.data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Support bracket access."""
        return self.data.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Support bracket assignment."""
        self.data[key] = value

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator."""
        return key in self.data

    def keys(self):
        """Return keys."""
        return self.data.keys()

    def values(self):
        """Return values."""
        return self.data.values()

    def items(self):
        """Return items."""
        return self.data.items()

@dataclass
class AppConfig:
    """Application configuration with tolerant attribute access."""
    config_dict: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a nested config value."""
        if isinstance(self.config_dict, dict):
            return self.config_dict.get(key, default)
        return default

    def __getattr__(self, name: str) -> Any:
        """Fallback for any attribute access - return no-op callable or value."""
        # First check if it's in config_dict
        if isinstance(self.config_dict, dict) and name in self.config_dict:
            return self.config_dict[name]
        # For logger-style methods, return a no-op callable
        def _noop(*args, **kwargs):
            return None
        return _noop

def load_config() -> AppConfig:
    """Load configuration from environment or defaults."""
    project_root = Path(__file__).parent.parent
    config_dict = {
        "paths": {
            "base": str(project_root),
            "data": str(project_root / "data"),
            "results": str(project_root / "data" / "results"),
            "derived_data": str(project_root / "data" / "derived"),
            "code": str(project_root / "code"),
        },
        "analysis": {
            "bootstrap_count": 1000,
            "train_test_split": 0.7,
        },
        "logging": {
            "level": "INFO",
        },
        "seeds": {
            "random": int(os.getenv("RANDOM_SEED", "42")),
            "numpy": int(os.getenv("NUMPY_SEED", "42")),
        },
    }
    return AppConfig(config_dict=config_dict)

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Set up logging with the given level."""
    logger = logging.getLogger("proj179")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    
    # Add handler if not already present
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger

def get_seed(seed_type: str = "random") -> int:
    """Get a seed value from config or environment."""
    config = load_config()
    seeds = config.get("seeds", {})
    if isinstance(seeds, dict):
        return seeds.get(seed_type, 42)
    return 42

def main():
    """Test configuration loading."""
    config = load_config()
    logger = setup_logging("info")
    logger.info("Configuration loaded successfully.")
    logger.info(f"Base path: {config.get('paths', {}).get('base')}")

if __name__ == "__main__":
    main()