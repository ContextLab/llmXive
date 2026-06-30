import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class AppConfig:
    """Configuration container for the application."""
    config: Dict[str, Any] = field(default_factory=dict)
    seed: int = 42
    log_level: str = "INFO"
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Tolerant get method to mimic dict-like access.
        Handles nested access like config.get('paths', {}).get('derived_data')
        by returning a nested dict or a tolerant object if key missing.
        """
        if key in self.config:
            val = self.config[key]
            if isinstance(val, dict):
                return TolerantDict(val)
            return val
        return default

class TolerantDict:
    """A dict-like wrapper that returns a TolerantDict or None for missing keys."""
    def __init__(self, data: Dict[str, Any]):
        self.data = data

    def get(self, key: str, default: Any = None) -> Any:
        val = self.data.get(key, default)
        if isinstance(val, dict):
            return TolerantDict(val)
        return val

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from a YAML file or return defaults."""
    from pyyaml import load as yaml_load, Loader
    import os
    
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = yaml_load(f, Loader=Loader)
        return AppConfig(config=config_data)
    return AppConfig()

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def get_seed(config: Optional[AppConfig] = None) -> int:
    """Get the random seed from config or default."""
    if config:
        return config.seed
    return 42

def main():
    """Main entry point for config module (for testing)."""
    config = load_config()
    print(f"Loaded config: {config.config}")
    print(f"Seed: {config.seed}")
    print(f"Log level: {config.log_level}")

if __name__ == "__main__":
    main()
