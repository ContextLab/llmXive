import random
import numpy as np

def test_seeds_are_pinned():
    # After importing the seeds module, the global RNG state should be deterministic
    import code.utils.seeds  # noqa: F401

    # The first few values should be reproducible
    assert random.random() == 0.6394267984578837
    assert np.random.rand() == 0.3745401188473625
    # If torch is available, its seed is also set – we cannot assert a value without torch
    # but the import should not raise an exception.