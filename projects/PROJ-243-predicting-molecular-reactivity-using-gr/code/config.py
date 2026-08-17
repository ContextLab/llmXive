import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

class Config:
    """Configuration class for the project."""
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or os.getcwd()
        self.seed = 42
        self.device = 'cpu'
        self.log_level = logging.INFO

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """Return the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config_instance
    _config_instance = config

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = get_config().seed
    random.seed(seed)
    np.random.seed(seed)
    # Note: torch seed setting is handled in model scripts if torch is available

def ensure_directories() -> None:
    """
    Ensure all necessary project directories exist based on the current config.
    This is a helper for setup scripts.
    """
    config = get_config()
    base = config.project_root
    
    # Define the directory structure required by the project
    # This matches the paths in tasks.md (Phase 1)
    directories = [
        "data/raw",
        "data/processed",
        "data/assets",
        "code",
        "artifacts",
        "tests",
        "artifacts/logs",
        "artifacts/weights",
        "figures"
    ]
    
    for dir_path in directories:
        full_path = os.path.join(base, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)

def get_default_config() -> Dict[str, Any]:
    """Return a dictionary of default configuration values."""
    return {
        "seed": 42,
        "device": "cpu",
        "log_level": logging.INFO
    }
