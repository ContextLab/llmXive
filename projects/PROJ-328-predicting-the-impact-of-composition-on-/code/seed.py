import random
import os
import numpy as np

def set_seed(seed: int = 42) -> None:
    """Set the random seed for reproducibility across libraries."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)

def get_seed_env_vars() -> dict:
    """Return a dictionary of environment variables related to seeding."""
    return {
        "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED", "42"),
        "PYTHONHASHSEED_VAL": os.environ.get("PYTHONHASHSEED", "42")
    }

def apply_seed_env_vars() -> None:
    """Apply seed-related environment variables to the current process."""
    seed = os.environ.get("PYTHONHASHSEED", "42")
    os.environ["PYTHONHASHSEED"] = str(seed)

def init_reproducibility(seed: int = 42) -> None:
    """Initialize all reproducibility settings."""
    set_seed(seed)
    apply_seed_env_vars()