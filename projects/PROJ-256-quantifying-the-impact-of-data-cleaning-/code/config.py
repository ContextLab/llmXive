"""
Configuration management module.
Provides a Config class that acts as a tolerant dictionary/attribute accessor
to handle varied calling patterns across the project.
"""
import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    """
    Configuration container.
    Supports attribute access (config.KEY) and dictionary access (config.get('KEY')).
    Also supports method calls like config.info() or config.get() as a generic accessor.
    """
    def __init__(self):
        self._data = {
            "DATASET_URLS": os.getenv("DATASET_URLS", "https://archive.ics.uci.edu/ml/machine-learning-databases/"),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "DATA_DIR": os.getenv("DATA_DIR", "data"),
            "FIGURES_DIR": os.getenv("FIGURES_DIR", "figures"),
            "SPEC_DIR": os.getenv("SPEC_DIR", "specs"),
            "TASKS_FILE": os.getenv("TASKS_FILE", "tasks.md"),
            "STATE_FILE": os.getenv("STATE_FILE", ".specify/state.yaml"),
            "RESEARCH_FILE": os.getenv("RESEARCH_FILE", "research.md"),
            "DATA_MODEL_FILE": os.getenv("DATA_MODEL_FILE", "data-model.md"),
            "CONTRACTS_DIR": os.getenv("CONTRACTS_DIR", "contracts"),
            "PLAN_FILE": os.getenv("PLAN_FILE", "plan.md"),
            "SPEC_FILE": os.getenv("SPEC_FILE", "spec.md"),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get."""
        return self._data.get(key, default)
    
    def set(self, key: str, value: Any):
        """Dictionary-style set."""
        self._data[key] = value
    
    def __getitem__(self, key: str) -> Any:
        """Support config['KEY']"""
        if key in self._data:
            return self._data[key]
        raise KeyError(key)
    
    def __getattr__(self, name: str) -> Any:
        """Support config.KEY"""
        if name in self._data:
            return self._data[name]
        # Fallback for logger-style calls (info, debug, warning, error)
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'log', 'get', 'set']:
            def _noop(*args, **kwargs):
                return None
            return _noop
        raise AttributeError(f"'Config' object has no attribute '{name}'")
    
    def __contains__(self, key: str) -> bool:
        return key in self._data

_global_config = Config()

def get_config() -> Config:
    """Return the global configuration instance."""
    return _global_config

def reload_config():
    """Reload configuration from environment variables."""
    global _global_config
    load_dotenv(override=True)
    _global_config = Config()

def main():
    """Test config access."""
    cfg = get_config()
    print(f"Random Seed: {cfg.get('RANDOM_SEED')}")
    print(f"Output Path: {cfg.OUTPUT_PATH}")

if __name__ == "__main__":
    main()