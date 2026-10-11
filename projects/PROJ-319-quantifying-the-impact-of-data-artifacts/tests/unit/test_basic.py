"""
Basic sanity test to ensure the test suite is discovered and configuration constants are correct.
"""

def test_noise_levels():
    """
    Verify that the default noise levels are defined as expected.
    """
    from code.config import NOISE_LEVELS
    assert NOISE_LEVELS == [0.01, 0.05, 0.10]
