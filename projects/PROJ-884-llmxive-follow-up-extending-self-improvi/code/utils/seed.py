import random
import os
import hashlib
import numpy as np
from typing import Optional, Dict, Any, List

_current_seed: Optional[int] = None
_seed_history: List[int] = []

def set_seed(seed: int):
    """
    Set the random seed for reproducibility across all libraries.
    
    Args:
        seed: Integer seed value
    """
    global _current_seed
    _current_seed = seed
    _seed_history.append(seed)
    
    # Set Python random seed
    random.seed(seed)
    
    # Set Python hash seed for reproducibility in dict/set ordering
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Set NumPy random seed if available
    try:
        np.random.seed(seed)
    except ImportError:
        pass

def get_seed() -> Optional[int]:
    """Get the current random seed."""
    return _current_seed

def get_seed_history() -> List[int]:
    """Get the history of all seeds set during execution."""
    return _seed_history.copy()

def generate_seed_from_string(input_string: str) -> int:
    """
    Generate a deterministic seed from a string input.
    
    Args:
        input_string: Input string to generate seed from
        
    Returns:
        Integer seed value
    """
    hash_obj = hashlib.md5(input_string.encode())
    return int(hash_obj.hexdigest(), 16) % (2**32)

def reset_seed():
    """Reset to default random state."""
    global _current_seed
    _current_seed = None
    random.seed()
    try:
        np.random.seed()
    except ImportError:
        pass

def set_deterministic_mode(seed: int = 42):
    """
    Set up deterministic mode with a default seed.
    
    Args:
        seed: Default seed value (default: 42)
    """
    set_seed(seed)

def main():
    """Demonstrate seed functionality."""
    set_seed(42)
    print(f"Seed set to: {get_seed()}")
    print(f"Random number (Python): {random.random()}")
    
    try:
        print(f"Random number (NumPy): {np.random.random()}")
    except ImportError:
        print("NumPy not available")
    
    reset_seed()
    print(f"Seed after reset: {get_seed()}")

if __name__ == "__main__":
    main()