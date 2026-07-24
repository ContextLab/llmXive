import os
import random
import numpy as np
from pathlib import Path
from typing import Final, Dict, Any

# Constants
MAX_TOKENS: Final[int] = 200
TIMEOUT_SECONDS: Final[int] = 300
SEED: Final[int] = 42
RAM_THRESHOLD_GB: Final[float] = 7.0

def set_seed(seed: int = SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def ensure_dirs_exist():
    """Ensure required directories exist."""
    dirs = [
        "data",
        "data/raw",
        "data/intermediate",
        "data/processed",
        "figures"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
