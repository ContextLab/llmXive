import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

class ConfigurationError(Exception):
    """Error in configuration loading."""
    pass

def load_env_vars() -> Dict[str, str]:
    """Load environment variables for configuration."""
    env_vars = {}
    
    # Load API keys if present
    if 'NASA_EXOPLANET_API_KEY' in os.environ:
        env_vars['api_key'] = os.environ['NASA_EXOPLANET_API_KEY']
    
    return env_vars

def set_random_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logging.info(f"Random seed set to {seed}")

def get_config() -> Dict[str, Any]:
    """Get pipeline configuration."""
    config = {
        "random_seed": 42,
        "cpu_threads": 1,
        "max_memory_gb": 6,
        "data_dirs": {
            "raw": "data/raw",
            "processed": "data/processed",
            "results": "results"
        },
        "logging": {
            "level": logging.INFO,
            "file": "logs/pipeline.log"
        }
    }
    
    # Load environment variables
    env_vars = load_env_vars()
    config.update(env_vars)
    
    return config

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration."""
    required_keys = ["random_seed", "cpu_threads", "max_memory_gb"]
    
    for key in required_keys:
        if key not in config:
            raise ConfigurationError(f"Missing required config key: {key}")
    
    if not isinstance(config["random_seed"], int):
        raise ConfigurationError("random_seed must be an integer")
    
    if config["cpu_threads"] < 1:
        raise ConfigurationError("cpu_threads must be at least 1")
    
    return True

def main():
    """Main entry point for config module."""
    config = get_config()
    validate_config(config)
    set_random_seed(config["random_seed"])
    
    logging.info("Configuration loaded successfully")
    return config

if __name__ == "__main__":
    main()
