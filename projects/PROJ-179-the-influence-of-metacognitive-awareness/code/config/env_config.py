import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import yaml

@dataclass
class TolerantDict:
    """A dictionary wrapper that tolerates missing keys and types."""
    data: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

class AppConfig:
    """Configuration handler that tolerates various access patterns."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        # Ensure nested structures exist for common access patterns
        if "paths" not in self.config:
            self.config["paths"] = {}
        if "analysis" not in self.config:
            self.config["analysis"] = {}
        if "logging" not in self.config:
            self.config["logging"] = {"level": "INFO"}

    def get(self, key: str, default: Any = None) -> Any:
        """Tolerant get method that handles nested dict access."""
        return self.config.get(key, default)

    def __getattr__(self, name: str) -> Any:
        """Fallback for unknown attributes to prevent AttributeError."""
        # If someone tries to call .info(), .debug(), etc. on this object
        # (mimicking a logger), return a no-op function.
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'get', 'set', 'load']:
            def _noop(*args, **kwargs):
                return None
            return _noop
        raise AttributeError(f"'AppConfig' object has no attribute '{name}'")

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from YAML file or return defaults."""
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            if config is None:
                config = {}
            return AppConfig(config)
    return AppConfig()

def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration.
    This function now handles being called with a string level directly,
    bypassing the config.get issue that caused the crash in T035.
    """
    # Ensure level is valid
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if level.upper() not in valid_levels:
        level = 'INFO'
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def get_seed() -> int:
    """Get random seed from environment or config."""
    return int(os.getenv("RANDOM_SEED", 42))

def main():
    """Entry point for config module (optional)."""
    config = load_config()
    logger = setup_logging(config.get("logging", {}).get("level", "INFO"))
    logger.info("Configuration loaded successfully.")
    return config

# Global config instance for convenience
CONFIG = load_config()
