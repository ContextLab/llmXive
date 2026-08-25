"""
Global random seed pinning module for reproducibility.

This module enforces Constitution Principle I by setting global random seeds
for numpy, torch, and the standard library random module to a fixed value (42).

Usage:
    Import this module at the very beginning of any script that requires
    reproducibility. The seed will be set immediately upon import.
    
    from utils.seed import set_global_seed
    
    # Or simply:
    import utils.seed  # This triggers the seed setting via side effect
"""

import random
import os
import sys
from typing import Optional

# Try to import numpy and torch, but make them optional dependencies
# to avoid breaking scripts that don't use them
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Default seed value as specified in the task
DEFAULT_SEED = 42

# Track if seed has been set to avoid redundant operations
_seed_set = False

def set_global_seed(seed: Optional[int] = None) -> int:
    """
    Set global random seeds for reproducibility across all libraries.
    
    Args:
        seed: The seed value to use. Defaults to DEFAULT_SEED (42).
    
    Returns:
        The seed value that was set.
    
    Raises:
        ValueError: If the seed is negative.
    """
    global _seed_set
    
    if seed is None:
        seed = DEFAULT_SEED
    
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")
    
    # Set seed for standard library random module
    random.seed(seed)
    
    # Set seed for numpy if available
    if NUMPY_AVAILABLE:
        np.random.seed(seed)
    
    # Set seed for torch if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        # Additional torch reproducibility settings
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Set environment variable for additional reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    _seed_set = True
    
    return seed

def get_seed_status() -> dict:
    """
    Get the current status of seed setting.
    
    Returns:
        A dictionary containing:
        - 'seed_set': Whether the seed has been set
        - 'numpy_available': Whether numpy is available
        - 'torch_available': Whether torch is available
    """
    return {
        'seed_set': _seed_set,
        'numpy_available': NUMPY_AVAILABLE,
        'torch_available': TORCH_AVAILABLE
    }

# Execute seed setting on module import to ensure reproducibility
# This is the key mechanism for enforcing Constitution Principle I
if __name__ == "__main__":
    # If run as a script, demonstrate the functionality
    import argparse
    
    parser = argparse.ArgumentParser(description="Set global random seeds for reproducibility")
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED, 
                      help=f'Seed value to use (default: {DEFAULT_SEED})')
    parser.add_argument('--show-status', action='store_true',
                      help='Show current seed status')
    
    args = parser.parse_args()
    
    if args.show_status:
        status = get_seed_status()
        print(f"Seed status: {status}")
    else:
        set_global_seed(args.seed)
        print(f"Global seed set to {args.seed}")
        print(f"Status: {get_seed_status()}")
else:
    # Automatically set seed when imported (side effect)
    # This ensures reproducibility even if the script doesn't explicitly call set_global_seed
    set_global_seed(DEFAULT_SEED)