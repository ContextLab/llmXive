"""
Ensure that the global seed wrapper works deterministically.

The test imports ``src.seed`` (which simply calls ``src.config.set_seed`` at
import time) and checks that two separate imports produce the same RNG
state.
"""

import importlib
import sys

import numpy as np

# Import the seed module twice via importlib reload to simulate separate imports
seed_module = importlib.import_module("src.seed")
rng_state_1 = np.random.get_state()

# Reload the module – it should reset the seed to the same value
importlib.reload(seed_module)
rng_state_2 = np.random.get_state()

assert rng_state_1 == rng_state_2, "RNG state should be identical after re‑importing src.seed"