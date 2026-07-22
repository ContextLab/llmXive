import os
from typing import Optional, Dict, Any

# Default configuration values
DEFAULTS = {
    "seed": 42,
    "batch_size": 8,
    "recursion_depth": 2,
    "learning_rate": 1e-4,
    "token_limit": 100000,
    "max_memory_gb": 7,
}

class Config:
    def __init__(self, overrides: Optional[Dict[str, Any]] = None):
        self.seed = DEFAULTS["seed"]
        self.batch_size = DEFAULTS["batch_size"]
        self.recursion_depth = DEFAULTS["recursion_depth"]
        self.learning_rate = DEFAULTS["learning_rate"]
        self.token_limit = DEFAULTS["token_limit"]
        self.max_memory_gb = DEFAULTS["max_memory_gb"]

        if overrides:
            for key, value in overrides.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def __repr__(self) -> str:
      return f"Config(seed={self.seed}, batch_size={self.batch_size}, recursion_depth={self.recursion_depth}, learning_rate={self.learning_rate}, token_limit={self.token_limit})"

# Singleton instance for global access if needed, though explicit passing is preferred
_config_instance = Config()

def get_config() -> Config:
    return _config_instance

def validate_config(config: Config) -> bool:
    """
    Validates the configuration against CPU-only constraints and logical bounds.
    Returns True if valid, raises ValueError otherwise.
    """
    if config.recursion_depth < 1:
        raise ValueError(f"Recursion depth must be >= 1, got {config.recursion_depth}")
    if config.recursion_depth > 2:
        raise ValueError(f"Recursion depth must be <= 2 for CPU constraints, got {config.recursion_depth}")
    if config.batch_size < 1:
        raise ValueError(f"Batch size must be >= 1, got {config.batch_size}")
    if config.token_limit < 1000:
        raise ValueError(f"Token limit must be >= 1000 for meaningful training, got {config.token_limit}")
    
    # Enforce CPU-only constraint logically (hardware check is done in runner)
    # We ensure no GPU-related flags are set if they existed
    return True
