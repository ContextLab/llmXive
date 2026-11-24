"""
Seed manager utility for the research pipeline.

This module ensures that all random number generators used in the
pipeline (Python's ``random``, NumPy, and PyTorch) are seeded with the
deterministic seed defined in ``code.config.SEED``.  Importing this
module automatically applies the seed so that downstream code can rely
on reproducible behaviour without needing to call any function
explicitly.

The implementation re‑uses the ``set_global_seed`` helper defined in
``code.config`` to keep the seeding logic in a single place.
"""

import random
import numpy as np
import torch

from code.config import SEED, set_global_seed

def seed_all() -> None:
    """Seed Python, NumPy and PyTorch RNGs using the configured seed."""
    # ``set_global_seed`` already seeds ``random``, ``numpy`` and ``torch``.
    set_global_seed(SEED)

# Apply the seed as soon as the module is imported.
seed_all()