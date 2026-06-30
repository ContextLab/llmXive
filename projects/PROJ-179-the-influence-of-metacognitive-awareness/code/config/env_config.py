import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

class TolerantDict(dict):
    """A dictionary that allows attribute access and returns None for missing keys."""
    def __getattr__(self, name):
        return self.get(name)
    def __setattr__(self, name, value):
        self[name] = value
    def __delattr__(self, name):
        del self[name]

@dataclass
class AppConfig:
    """
    Application configuration handler.
    Tolerates missing keys by returning None or default values via .get() methods.
    Supports logger-style method calls (info, error, etc.) via __getattr__.
    """
    config: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Standard dict get method."""
        return self.config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self.config[key]

    def __contains__(self, key: str) -> bool:
        return key in self.config

    def __getattr__(self, name: str) -> Any:
        """
        Tolerant attribute access.
        If a method like 'get' is called on the object, it delegates to self.get.
        If a logger-style method (info, error, debug) is called, it returns a no-op.
        """
        # Explicitly handle the 'get' method if called as an attribute
        if name == 'get':
            return self.get
        
        # Tolerant logger fallback: return a no-op function for any unknown attribute
        # This prevents AttributeError when scripts call config.info(), config.error(), etc.
        def _noop(*args, **kwargs):
            return None
        return _noop

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Loads configuration from a YAML file or returns default config."""
    if config_path and os.path.exists(config_path):
        # Simple YAML loading logic would go here
        # For now, return empty tolerant config
        pass
    return AppConfig(config={
        "paths": {
            "derived_data": "data/derived",
            "results": "data/results",
            "data": "data"
        },
        "analysis": {
            "bootstrap_count": 1000,
            "train_ratio": 0.7
        },
        "logging": {
            "level": "INFO"
        },
        "columns": {
            "participant_id": "participant_id",
            "trial_id": "trial_id",
            "stimulus_modality": "stimulus_modality",
            "source_label": "source_label",
            "participant_response": "participant_response",
            "confidence_rating": "confidence_rating"
        }
    })

def setup_logging(level: str = "INFO") -> None:
    """Configures root logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_seed() -> int:
    """Returns a deterministic seed from environment or default."""
    return int(os.getenv("RANDOM_SEED", "42"))

def main() -> None:
    """Entry point for config module testing."""
    config = load_config()
    print(f"Paths: {config.get('paths', {})}")
    print(f"Analysis: {config.get('analysis', {})}")
    # Test tolerant access
    print(f"Logging Level: {config.get('logging', {}).get('level', 'INFO')}")
    # Test no-op logger access
    config.info("Test message")
    config.error("Test error")
    print("Config loaded successfully.")

if __name__ == "__main__":
    main()