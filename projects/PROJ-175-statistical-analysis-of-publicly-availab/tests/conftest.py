"""
Pytest configuration and fixtures.
"""
import os
import sys
import random
import numpy as np

# Import the global seed configuration from the code package
from code import SEED, set_global_seed

def pytest_configure(config):
    """Set global seeds at test start."""
    # Use the centralized seed value and setter
    set_global_seed(SEED)
    
    # Ensure PYTHONPATH includes the code directory
    root_dir = os.path.dirname(os.path.dirname(__file__))
    code_dir = os.path.join(root_dir, "code")
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)