"""
Test that the project‑wide reproducibility constants are correctly applied.

The test imports ``code.utils.constants`` which sets the seeds for NumPy and
the built‑in ``random`` module.  After import, the first random draws must
match the deterministic values produced by those seeds.
"""
import importlib

# Import the constants module – this has the side‑effect of seeding RNGs
constants = importlib.import_module("code.utils.constants")
SEED = constants.SEED

# Verify that the constant is the expected integer (seed 0 is used in the
# implementation).
assert isinstance(SEED, int), "SEED should be an integer"
assert SEED == 0, f"Expected SEED == 0, got {SEED}"

# After the import the global RNGs are seeded.  The first draws should be
# reproducible and match the known values for seed 0.
import numpy as np
import random

# NumPy first random value after seeding with 0
np_val = np.random.rand()
assert abs(np_val - 0.5488135039273248) < 1e-12, f"Unexpected NumPy first value: {np_val}"

# Python's random first value after seeding with 0
py_val = random.random()
assert abs(py_val - 0.8444218515250481) < 1e-12, f"Unexpected random.random() first value: {py_val}"