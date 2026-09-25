import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

from utils import setup_logging

logger = setup_logging("config")

class ConfigurationError(Exception):
    pass

def load_env_vars() -> Dict[str, str]:
    """Loads environment variables."""
    return {
        "API_KEY": os.getenv("API_KEY", ""),
        "DATA_DIR": os.getenv("DATA_DIR", "data"),
    }

def set_random_seed(seed: int = 42) -> None:
    """Sets random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seed set to {seed}")

class Configuration:
    def __init__(self, data_dir: Optional[str] = None, seed: int = 42):
        self.data_dir = Path(data_dir) if data_dir else Path(os.getenv("DATA_DIR", "data"))
        self.seed = seed
        self.threads = int(os.getenv("CPU_THREADS", "1"))
        self.max_memory_gb = int(os.getenv("MAX_MEMORY_GB", "6"))
        
        # Validate paths
        if not self.data_dir.exists():
            logger.warning(f"Data directory {self.data_dir} does not exist. Creating it.")
            self.data_dir.mkdir(parents=True, exist_ok=True)

def get_config() -> Configuration:
    """
    Returns a global Configuration object.
    Handles the case where config might be a dict in some execution contexts
    by ensuring we return a proper Configuration object.
    """
    # Check if a global config is already set
    global _config
    if '_config' not in globals():
        _config = Configuration()
    return _config

def validate_config(config: Configuration) -> bool:
    """Validates the configuration."""
    if not config.data_dir.exists():
        raise ConfigurationError(f"Data directory {config.data_dir} does not exist.")
    return True

def main():
    """Main entry point for config module."""
    config = get_config()
    validate_config(config)
    logger.info(f"Configuration loaded: {config}")

if __name__ == "__main__":
    main()
