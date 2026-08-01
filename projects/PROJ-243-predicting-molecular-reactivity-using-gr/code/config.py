import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

class Config:
    """Configuration management for the project."""
    
    def __init__(self):
        self._config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment or defaults."""
        return {
            "paths": {
                "raw": os.path.join("data", "raw"),
                "processed": os.path.join("data", "processed"),
                "assets": os.path.join("data", "assets"),
                "code": "code",
                "artifacts": "artifacts",
                "tests": "tests",
                "logs": os.path.join("artifacts", "logs")
            },
            "random_seed": 42,
            "device": "cpu",
            "logging_level": logging.INFO
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

_config_instance = None

def get_config() -> Dict[str, Any]:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance._config

def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    config = get_config()
    paths = config["paths"]
    
    required_dirs = [
        paths["raw"],
        paths["processed"],
        paths["assets"],
        paths["code"],
        paths["artifacts"],
        paths["tests"],
        paths["logs"]
    ]
    
    for dir_path in required_dirs:
        os.makedirs(dir_path, exist_ok=True)

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seed for reproducibility."""
    if seed is None:
        seed = get_config()["random_seed"]
        
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    logging.info(f"Random seed set to: {seed}")
