"""
Pytest configuration and fixtures.
"""
import os
import sys
import random
import numpy as np

# Import the global seed configuration from the code package
# Note: We import from the code package root. If __init__.py defines SEED and set_global_seed,
# we use them. If not, we define them here to ensure tests pass.
try:
    from code import SEED, set_global_seed
except ImportError:
    # Fallback if code/__init__.py is not fully set up or missing these names
    SEED = 42
    def set_global_seed(seed):
        random.seed(seed)
        np.random.seed(seed)
        if 'torch' in sys.modules:
            import torch
            torch.manual_seed(seed)

def pytest_configure(config):
    """Set global seeds at test start."""
    # Use the centralized seed value and setter
    set_global_seed(SEED)
    
    # Ensure PYTHONPATH includes the code directory
    root_dir = os.path.dirname(os.path.dirname(__file__))
    code_dir = os.path.join(root_dir, "code")
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    
    # Ensure tests directory is also accessible if needed
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)