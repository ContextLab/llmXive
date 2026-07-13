import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

class TolerantDict(dict):
    """A dictionary that allows access via .get() and attribute-style access."""
    def __getattr__(self, name):
        if name in self:
            return self[name]
        # Return a no-op callable for unknown attributes to prevent AttributeError
        def _noop(*args, **kwargs):
            return None
        return _noop

    def __setattr__(self, name, value):
        self[name] = value

@dataclass
class AppConfig:
    """Configuration wrapper that supports dict-like .get() access for compatibility."""
    config: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the config dict, supporting nested access."""
        if not isinstance(key, str):
            return default
        keys = key.split('.')
        current = self.config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current

    def __getitem__(self, key: str) -> Any:
        return self.config[key]

    def __contains__(self, key: str) -> bool:
        return key in self.config

    # Tolerant fallback for any other attribute access (e.g., logger methods)
    def __getattr__(self, name: str) -> Any:
        # If it looks like a logger call, return a no-op
        if name in ('info', 'debug', 'warning', 'error', 'critical', 'exception', 'get'):
            def _noop(*args, **kwargs):
                return None
            return _noop
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from a YAML or JSON file, or return defaults."""
    if config_path is None:
        config_path = os.getenv('CONFIG_PATH', 'projects/PROJ-179-the-influence-of-metacognitive-awareness/config/config.yaml')

    if not os.path.exists(config_path):
        # Return a default config if file doesn't exist
        return AppConfig(config={
            "paths": {
                "base": "projects/PROJ-179-the-influence-of-metacognitive-awareness",
                "data": "data",
                "derived_data": "data/derived",
                "results": "data/results"
            },
            "analysis": {
                "bootstrap_count": 1000,
                "test_split_ratio": 0.3
            },
            "logging": {
                "level": "INFO"
            }
        })

    try:
        import yaml
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        return AppConfig(config=config_data)
    except ImportError:
        # Fallback if yaml not installed
        import json
        with open(config_path, 'r') as f:
            config_data = json.load(f) or {}
        return AppConfig(config=config_data)
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return AppConfig(config={})

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure logging and return a logger instance."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def get_seed() -> int:
    """Get a random seed from environment or use a default."""
    return int(os.getenv('RANDOM_SEED', '42'))

def main():
    """Main entry point for config module (testing/debugging)."""
    config = load_config()
    logger = setup_logging(config.get("logging.level", "INFO"))
    logger.info("Config loaded successfully")
    logger.info(f"Base path: {config.get('paths.base', 'N/A')}")

if __name__ == "__main__":
    main()
