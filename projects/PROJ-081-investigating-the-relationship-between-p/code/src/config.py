"""
config.py
----------
Global configuration for the project, including fixed random seeds to ensure
reproducibility across all analyses.
"""

import random
import numpy as np

# Fixed seeds for reproducibility
np.random.seed(42)
random.seed(42)

# Scikit‑learn compatible random_state value
random_state = 42
