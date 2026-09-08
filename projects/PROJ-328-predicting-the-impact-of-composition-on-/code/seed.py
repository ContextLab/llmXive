"""
Reproducibility and seeding utilities.
"""
import random
import os
import numpy as np
from typing import Optional

def set_seed(seed: int = 42):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed_env_vars() -> int:
    """Get seed from environment variable or default to 42."""
    return int(os.environ.get('PYTHONHASHSEED', '42'))

def apply_seed_env_vars():
    """Apply seed from environment variables."""
    seed = get_seed_env_vars()
    set_seed(seed)

def init_reproducibility(seed: Optional[int] = None):
    """Initialize reproducibility settings."""
    if seed is not None:
        set_seed(seed)
    else:
        apply_seed_env_vars()
