import os
import random
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import sys

class Config:
    def __init__(self):
        self.seed = int(os.getenv("RANDOM_SEED", "42"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.mp_api_key = os.getenv("MP_API_KEY", "")

_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config() -> None:
    global _config_instance
    _config_instance = None

def initialize_environment() -> None:
    """
    Initialize environment variables from a .env file if present.
    """
    # Simple implementation for .env loading
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

def main():
    cfg = get_config()
    print(f"Seed: {cfg.seed}")
    print(f"Log Level: {cfg.log_level}")
    print(f"MP API Key present: {bool(cfg.mp_api_key)}")

if __name__ == "__main__":
    initialize_environment()
    main()