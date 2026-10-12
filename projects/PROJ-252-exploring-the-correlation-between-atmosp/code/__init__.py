"""
Package initialization for the atmospheric pressure-earthquake project.
Sets deterministic random seeds for reproducibility (task T001).
"""
import random

import numpy as np

# Deterministic seeds for every entry point that imports the code package.
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
