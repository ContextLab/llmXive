"""Configuration management for the alloy prediction project."""
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from logging_config import get_logger


class Config:
    """Configuration class with tolerant attribute access."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "data/config.json"
        self.logger = get_logger()
        self._config = self._load_config()
        
        # Set default paths
        self.data_dir = Path(self._config.get("data_dir", "data"))
        self.data_raw_dir = self.data_dir / "raw"
        self.data_processed_dir = self.data_dir / "processed"
        self.data_logs_dir = self.data_dir / "logs"
        self.models_dir = Path(self._config.get("models_dir", "models"))
        self.results_dir = Path(self._config.get("results_dir", "results"))
        
        # Data paths (tolerant aliases)
        self.data_raw = self.data_raw_dir
        self.data_processed = self.data_processed_dir
        self.data_logs = self.data_logs_dir
        
        # Validation settings
        self.random_seed = self._config.get("random_seed", 42)
        self.valid_measurement_methods = self._config.get(
            "valid_measurement_methods", 
            r"(?i)(ultrasonic|direct|resonant|impulse)"
        )
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or return defaults."""
        config_path = Path(self.config_path)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                self.logger.log("config_load_warning", message="Using default config")
        return {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by key."""
        return self._config.get(key, default)
    
    def __getattr__(self, name: str) -> Any:
        """Tolerant attribute access - return no-op for unknown attributes."""
        # Return existing attributes first
        if hasattr(super(), name):
            return super().__getattribute__(name)
        
        # For unknown attributes, return a no-op callable
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


_CONFIG_INSTANCE: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """Get or create the global config instance."""
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None:
        _CONFIG_INSTANCE = Config(config_path)
    return _CONFIG_INSTANCE


def main():
    """Main entry point for config module."""
    config = get_config()
    print(f"Config loaded: {config.config_path}")
    print(f"Data directories: {config.data_dir}")
    return config


if __name__ == "__main__":
    main()
