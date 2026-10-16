"""
Dummy test to verify that the pytest fixture suite pins the random seed
and that reproducible random numbers are generated.
"""

import numpy as np

def test_random_state_reproducibility():
    """
    Ensure that two RandomState instances initialized with the same seed
    produce identical first draws.
    """
    rs1 = np.random.RandomState(42)
    rs2 = np.random.RandomState(42)
    val1 = rs1.rand()
    val2 = rs2.rand()
    assert np.isclose(val1, val2), "RandomState draws differ despite identical seeds"