"""
Reproducibility utilities for the project.

This module defines a single seed constant and pins the random number
generators of NumPy, the Python ``random`` module, and scikit‑learn‑compatible
utilities to that seed. Importing this module has the side‑effect of
setting the seeds, ensuring deterministic behaviour across the entire
code‑base.
"""
import numpy as np
import random

# The seed value used throughout the project.  Keeping it in a single
# location makes it easy to change reproducibility settings globally.
SEED: int = 0

# Pin NumPy's RNG
np.random.seed(SEED)

# Pin Python's built‑in RNG
random.seed(SEED)

# scikit‑learn relies on NumPy's RNG for most algorithms, but some
# utilities accept a ``random_state`` integer directly.  By exposing the
# constant we make it clear that any ``random_state`` arguments should
# be set to ``SEED``.
__all__ = ["SEED"]
