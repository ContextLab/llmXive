"""
Configuration and random seed management.
"""
import os
import random
import numpy as np
from typing import Optional

def set_random_seed(seed: int = 42):
    """Pin random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config_value(key: str, default=None):
    """Get configuration value from environment or default."""
    return os.getenv(key, default)

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv('DEBUG_MODE', 'false').lower() == 'true'

def main():
    """CLI entry point for config checks."""
    print(f"Debug Mode: {is_debug_mode()}")
    print(f"Random Seed: {os.getenv('RANDOM_SEED', '42')}")

if __name__ == "__main__":
    main()
