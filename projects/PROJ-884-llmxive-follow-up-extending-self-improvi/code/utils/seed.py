import random
import os
import hashlib
from typing import Optional, Dict, Any

_current_seed: Optional[int] = None

def set_seed(seed: int):
    """
    Set the random seed for reproducibility.
    
    Args:
        seed: Integer seed value
    """
    global _current_seed
    _current_seed = seed
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> Optional[int]:
    """Get the current random seed."""
    return _current_seed

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
    print(f"Random number: {random.random()}")
    
    reset_seed()
    print(f"Seed after reset: {get_seed()}")

if __name__ == "__main__":
    main()
