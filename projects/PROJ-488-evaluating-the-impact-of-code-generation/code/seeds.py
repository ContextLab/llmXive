import random
from typing import Optional
import numpy as np

SEED_VALUE = 42

def set_seed(seed: Optional[int] = None):
    """
    Sets the random seed for reproducibility.
    
    Args:
        seed: The seed value. Defaults to SEED_VALUE.
    """
    if seed is None:
        seed = SEED_VALUE
        
    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed_value() -> int:
    """
    Returns the current seed value.
    
    Returns:
        The seed value.
    """
    return SEED_VALUE

def main():
    """
    Main entry point for seed utilities.
    """
    print(f"Seed value: {get_seed_value()}")
    set_seed()
    print(f"Random number after setting seed: {random.random()}")

if __name__ == "__main__":
    main()
