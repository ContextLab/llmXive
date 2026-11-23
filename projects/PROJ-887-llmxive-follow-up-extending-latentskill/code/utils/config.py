"""
Reproducibility utilities for the project.

This module sets a global random seed, defines project‑wide path constants
using the `llmxive_toolkit.paths` helpers, and provides a small constant
`OOD_THRESHOLD` used throughout the code base.

Importing this module prints the seed and the resolved path values, which
serves as a quick verification that the configuration has been applied.
"""

import random
import numpy as np

# Import the llmxive path helpers
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Global random seed
# ----------------------------------------------------------------------
SEED = 42

def _set_global_seed(seed: int = SEED) -> None:
    """Set the global random seed for Python, NumPy and (if available) PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        # Torch is optional; ignore if not installed
        pass

# Apply the seed as soon as the module is imported
_set_global_seed()

# ----------------------------------------------------------------------
# Project‑wide path constants
# ----------------------------------------------------------------------
# The `paths` helper creates the required directories if they do not exist.
DATA_ROOT = paths.root
DATA_RAW = paths.data("raw")
DATA_PROCESSED = paths.data("processed")
DATA_RESULTS = paths.results()
DATA_FIGURES = paths.figures()
DATA_DOCS = paths.docs()
DATA_CODE = paths.code()

# ----------------------------------------------------------------------
# Miscellaneous constants
# ----------------------------------------------------------------------
OOD_THRESHOLD = 0.5

# ----------------------------------------------------------------------
# Verification output
# ----------------------------------------------------------------------
# Printing these values on import satisfies the verification step described
# in the task checklist.
print(f"[config] Seed set to {SEED}")
print("[config] Resolved paths:")
print(f"  DATA_ROOT      = {DATA_ROOT}")
print(f"  DATA_RAW       = {DATA_RAW}")
print(f"  DATA_PROCESSED = {DATA_PROCESSED}")
print(f"  DATA_RESULTS   = {DATA_RESULTS}")
print(f"  DATA_FIGURES   = {DATA_FIGURES}")
print(f"  DATA_DOCS      = {DATA_DOCS}")
print(f"  DATA_CODE      = {DATA_CODE}")
