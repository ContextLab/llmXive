import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration manager that acts as a tolerant dictionary-like object."""
    
    def __init__(self):
        self._config = {
            "DATASET_URLS": os.getenv("DATASET_URLS", ""),
            "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "data/processed"),
            "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
            "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
            "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
            "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)
    
    def __getattr__(self, name: str):
        """Tolerant fallback for unknown attributes (logger-like calls)."""
        def _noop(*args, **kwargs):
            return None
        return _noop

_global_config = None

def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def reload_config():
    global _global_config
    _global_config = Config()

def main():
    pass

if __name__ == "__main__":
    print(get_config().get("RAW_DATA_PATH"))
