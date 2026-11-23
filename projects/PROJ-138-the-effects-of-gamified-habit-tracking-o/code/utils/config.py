"""
Configuration and random seed management.
"""
import os
import random
import numpy as np
from typing import Optional

def set_random_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a configuration value from environment variables."""
    return os.getenv(key, default)

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes')

def main():
    """CLI entry point for config checks."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    set_random_seed(args.seed)
    print(f"Random seed set to {args.seed}")

if __name__ == "__main__":
    main()
