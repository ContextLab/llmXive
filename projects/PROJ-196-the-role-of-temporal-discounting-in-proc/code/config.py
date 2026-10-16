import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
import yaml
import numpy as np

# Exposed constant for reproducibility
RANDOM_SEED = 20241010

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).resolve().parent.parent

def get_config() -> Dict[str, Any]:
    """Loads the main configuration file if it exists."""
    config_path = get_project_root() / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def get_config_value(key: str, default: Any = None) -> Any:
    """Retrieves a specific configuration value."""
    config = get_config()
    return config.get(key, default)

def get_random_state(offset: int = 0) -> np.random.RandomState:
    """
    Returns a NumPy RandomState instance for reproducibility.

    The seed is based on the module-level RANDOM_SEED constant,
    optionally offset by the provided integer.

    Args:
        offset: Integer offset added to the base seed.

    Returns:
        A NumPy RandomState seeded with RANDOM_SEED + offset.
    """
    # Prioritize an environment variable if present
    env_seed = os.environ.get("RANDOM_SEED")
    if env_seed is not None:
        try:
            seed = int(env_seed) + offset
        except ValueError:
            # Fallback to the constant seed if conversion fails
            seed = RANDOM_SEED + offset
    else:
        # Use the constant seed
        seed = RANDOM_SEED + offset

    return np.random.RandomState(seed)