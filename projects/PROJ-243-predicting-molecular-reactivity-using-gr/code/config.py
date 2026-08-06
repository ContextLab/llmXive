"""
Configuration management for the molecular reactivity prediction pipeline.
Handles random seeds, device settings, and directory initialization.
"""
import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

# Default configuration values
DEFAULT_CONFIG = {
    "seed": 42,
    "device": "cpu",  # Enforcing CPU-only as per project constraints
    "log_level": "INFO",
    "log_dir": "artifacts/logs",
    "metrics_file": "artifacts/metrics.json",
    "data_dir": "data",
    "code_dir": "code",
    "tests_dir": "tests",
    "artifacts_dir": "artifacts",
    "max_workers": 4,
    "batch_size": 32,
}

class Config:
    """Holds configuration parameters for the experiment."""
    
    def __init__(self, overrides: Optional[Dict[str, Any]] = None):
        self.seed = DEFAULT_CONFIG["seed"]
        self.device = DEFAULT_CONFIG["device"]
        self.log_level = DEFAULT_CONFIG["log_level"]
        self.log_dir = DEFAULT_CONFIG["log_dir"]
        self.metrics_file = DEFAULT_CONFIG["metrics_file"]
        self.data_dir = DEFAULT_CONFIG["data_dir"]
        self.code_dir = DEFAULT_CONFIG["code_dir"]
        self.tests_dir = DEFAULT_CONFIG["tests_dir"]
        self.artifacts_dir = DEFAULT_CONFIG["artifacts_dir"]
        self.max_workers = DEFAULT_CONFIG["max_workers"]
        self.batch_size = DEFAULT_CONFIG["batch_size"]
        
        if overrides:
            for key, value in overrides.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        
        # Ensure reproducibility
        self._set_seeds()

    def _set_seeds(self):
        """Set random seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        os.environ['PYTHONHASHSEED'] = str(self.seed)

_config_instance: Optional[Config] = None

def get_config(overrides: Optional[Dict[str, Any]] = None) -> Config:
    """Get the singleton configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config(overrides)
    elif overrides:
        # Update existing config if overrides provided
        for key, value in overrides.items():
            if hasattr(_config_instance, key):
                setattr(_config_instance, key, value)
    return _config_instance

def set_seed(seed: int):
    """Manually set the random seed and update config."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config({"seed": seed})
    else:
        _config_instance.seed = seed
        _config_instance._set_seeds()

def ensure_directories():
    """Create all required directories defined in the project structure."""
    config = get_config()
    directories = [
        config.data_dir,
        os.path.join(config.data_dir, "raw"),
        os.path.join(config.data_dir, "processed"),
        os.path.join(config.data_dir, "assets"),
        config.code_dir,
        config.tests_dir,
        config.artifacts_dir,
        config.log_dir,
        os.path.join(config.artifacts_dir, "logs"),
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.debug(f"Created directory: {directory}")
    
    return directories

def get_default_config() -> Dict[str, Any]:
    """Return a copy of the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()