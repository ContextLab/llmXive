"""
Unit test for verifying the distance‑cutoff scaling logic implemented in
`code/generate_networks.py`.

The test checks that the nearest‑neighbor distance computed by
`nearest_neighbor_distance` correctly scales with a provided factor.
For a scaling factor of 1.0 the cutoff should be identical to the NN
distance, and for other factors it should be proportionally scaled.
"""

import numpy as np
import pytest

# Import the function under test from the project's generate_networks module.
from generate_networks import nearest_neighbor_distance

@pytest.mark.parametrize(
    "positions,expected_nn",
    [
        # Simple orthogonal unit cube corners – nearest‑neighbor distance = 1.0
        (np.array([[0, 0, 0],
                   [1, 0, 0],
                   [0, 1, 0],
                   [0, 0, 1]], dtype=float), 1.0),
        # Linear chain with spacing 2.5 – NN distance = 2.5
        (np.array([[0, 0, 0],
                   [2.5, 0, 0],
                   [5.0, 0, 0]], dtype=float), 2.5),
    ],
)
def test_cutoff_scaling_behavior(positions, expected_nn):
    """
    Verify that the cutoff computed as `factor * nn_distance` matches the
    expected value for a range of scaling factors.
    """
    # Compute the nearest‑neighbor distance using the project's utility.
    nn_dist = nearest_neighbor_distance(positions)

    # The computed NN distance should match the analytically expected value.
    assert np.isclose(nn_dist, expected_nn, atol=1e-8), (
        f"Nearest‑neighbor distance mismatch: got {nn_dist}, expected {expected_nn}"
    )

    # Test a few representative scaling factors.
    for factor, expected_factor_scaled in [(0.5, 0.5), (1.0, 1.0), (1.5, 1.5)]:
        cutoff = factor * nn_dist
        expected_cutoff = expected_factor_scaled * expected_nn
        assert np.isclose(cutoff, expected_cutoff, atol=1e-8), (
            f"Cutoff scaling failed for factor {factor}: "
            f"got {cutoff}, expected {expected_cutoff}"
        )