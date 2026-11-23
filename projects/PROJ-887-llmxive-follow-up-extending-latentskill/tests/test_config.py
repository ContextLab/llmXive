"""
Unit test for the reproducibility configuration.

The test imports the `code.utils.config` module, which sets the global
random seed on import. It then checks that the first values drawn from the
Python `random` module and NumPy's RNG match the expected deterministic
results for seed 42.
"""

import importlib
import random
import numpy as np

def test_deterministic_rng():
    # Reload the config module to ensure the seed is (re)applied
    import code.utils.config as cfg
    importlib.reload(cfg)

    # After the import the RNGs should be in a known state
    r_python = random.random()
    r_numpy = np.random.rand()

    # Expected values for seed 42
    assert abs(r_python - 0.6394267984578837) < 1e-12, "Python RNG not deterministic"
    assert abs(r_numpy - 0.3745401188473625) < 1e-12, "NumPy RNG not deterministic"