"""
Project initialization with deterministic random seed management.
"""
import os
import numpy as np

# Set deterministic random seed
os.environ['PYTHONHASHSEED'] = '42'
np.random.seed(42)
SEED = 42
