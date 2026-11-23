"""
Dummy test to verify that the pytest configuration and fixtures work.
It checks that a fixed random seed produces reproducible values.
"""
import numpy as np

def test_random_state_reproducibility(seed):
    rs = np.random.RandomState(seed)
    val1 = rs.rand()
    rs2 = np.random.RandomState(seed)
    val2 = rs2.rand()
    assert val1 == val2, "RandomState with same seed should produce identical values"
