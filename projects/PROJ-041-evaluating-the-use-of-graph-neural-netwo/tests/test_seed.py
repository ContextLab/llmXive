import random
import numpy as np
from utils.seed import set_seed

def test_seed_reproducibility():
    """Verify that set_seed produces reproducible RNG state."""
    set_seed(42)
    r1 = random.random()
    n1 = np.random.rand()

    set_seed(42)
    r2 = random.random()
    n2 = np.random.rand()

    assert r1 == r2
    assert n1 == n2
