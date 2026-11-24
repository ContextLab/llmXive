"""
Random seed initialization module.

This module is imported at the start of the pipeline (e.g., in ``code/main.py``)
to ensure deterministic behaviour across runs. It sets the global seeds for
NumPy, Python's ``random`` module, and provides a constant ``RANDOM_STATE``
that can be used with scikit‑learn estimators.
"""

import os
import random

import numpy as np

# Fixed seed value for the entire project
SEED = 42

# Ensure reproducibility for Python's built‑in random module
random.seed(SEED)

# Ensure reproducibility for NumPy's random number generator
np.random.seed(SEED)

# Some libraries (e.g., PyTorch) respect the ``PYTHONHASHSEED`` environment
# variable for additional determinism; set it here for completeness.
os.environ["PYTHONHASHSEED"] = str(SEED)

# Provide a convenient constant for scikit‑learn functions that accept a
# ``random_state`` argument.
RANDOM_STATE = SEED

# The module performs its work on import; no public functions are required.
# Importing this file is sufficient to pin the seeds.
