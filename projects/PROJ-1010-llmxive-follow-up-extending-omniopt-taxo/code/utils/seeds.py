import os
import random
import hashlib
from typing import Optional, Dict, Any
import numpy as np

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed_from_hash(seed_string: str) -> int:
    """Generate a deterministic seed from a string."""
    return int(hashlib.sha256(seed_string.encode()).hexdigest(), 16) % (2**32)

def restore_seed(state: Dict[str, Any]) -> None:
    """Restore random state from a saved dictionary."""
    if 'random' in state:
        random.setstate(state['random'])
    if 'numpy' in state:
        np.random.set_state(state['numpy'])

def main():
    """Demonstrate seed setting."""
    seed = 42
    set_seed(seed)
    print(f"Seeds set to {seed}")

if __name__ == "__main__":
    main()
