"""
Unit test for NaN/infinite perplexity value detection.

This test is intentionally written before the implementation of the
`detect_invalid_perplexity` function in `code/model_metrics.py`. It should
fail until the function is correctly implemented.
"""

import pytest
import math
import numpy as np

# The function to be implemented in `code/model_metrics.py`
from code.model_metrics import detect_invalid_perplexity

def test_detect_invalid_perplexity():
    """
    Verify that `detect_invalid_perplexity` correctly identifies indices of
    NaN, positive infinity, and negative infinity values in a list of
    perplexity scores.
    """
    # Sample perplexity values including normal, NaN, and infinite entries
    perplexities = [
        12.3,                # valid
        float('nan'),       # NaN
        45.6,                # valid
        float('inf'),       # positive infinity
        -float('inf'),      # negative infinity
        78.9                 # valid
    ]

    # Expected indices of invalid values (NaN and infinities)
    expected_invalid_indices = {1, 3, 4}

    # Call the function under test
    invalid_indices = set(detect_invalid_perplexity(perplexities))

    # The test should fail until the function is correctly implemented
    assert invalid_indices == expected_invalid_indices, (
        f"Expected invalid indices {expected_invalid_indices}, "
        f"got {invalid_indices}"
    )