import random
import os
import sys
from typing import Optional

def set_global_seed(seed: int = 42):
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    if 'numpy' in sys.modules:
        import numpy as np
        np.random.seed(seed)
    if 'torch' in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def get_seed_status() -> dict:
    """Return current seed status."""
    return {
        'python': random.getstate()[1][0] if hasattr(random, 'getstate') else None,
        'seed_value': 42 # Default expected value
    }

if __name__ == "__main__":
    set_global_seed()
    print("Global seeds set.")
