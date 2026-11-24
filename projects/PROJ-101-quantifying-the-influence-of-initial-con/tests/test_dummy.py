"""
Dummy test to verify that the pytest fixture suite pins the random seed
correctly. The test creates two RandomState instances with the same seed
and checks that they produce identical values.
"""

import numpy as np

def test_random_state_reproducibility(seed):
    """
    The `seed` fixture provides the value 42. Using it to initialise
    NumPy's RandomState should yield the same first random number on each
    call.
    """
    rs1 = np.random.RandomState(seed)
    rs2 = np.random.RandomState(seed)

    val1 = rs1.rand()
    val2 = rs2.rand()

    assert np.isclose(val1, val2), "RandomState with same seed should be reproducible"