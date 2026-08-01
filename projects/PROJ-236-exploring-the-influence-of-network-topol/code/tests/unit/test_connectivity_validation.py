"""
Unit tests for the connectivity validation logic introduced in task T016.

The test generates a modest ensemble of random atomic configurations with a
fixed random seed, runs the validation routine, and asserts that at least
95 % of the realizations are connected.
"""

import pytest

from generate_networks import validate_connectivity_over_ensemble


@pytest.mark.parametrize(
    "num_realizations, n_atoms, factor, expected_rate",
    [
        # With a reasonable initial factor (1.0) and the default max_factor (2.0),
        # the algorithm should succeed for virtually all random point sets.
        (100, 30, 1.0, 0.95),
    ],
)
def test_connectivity_success_rate(num_realizations, n_atoms, factor, expected_rate):
    """
    Ensure that the connectivity validation reports a success rate ≥ 95 %.
    """
    # Use a deterministic seed so the test is reproducible.
    seed = 42
    success_rate, invalid = validate_connectivity_over_ensemble(
        num_realizations=num_realizations,
        n_atoms=n_atoms,
        factor=factor,
        seed=seed,
    )
    # The list of invalid realizations should be empty or very small.
    assert success_rate >= expected_rate, (
        f"Connectivity success rate {success_rate:.2f} is below the required "
        f"{expected_rate:.2f}"
    )
    # For extra safety we also assert that we did not exceed the allowed
    # failure budget (5 % of the ensemble).
    assert len(invalid) <= int((1 - expected_rate) * num_realizations)  # type: ignore


def test_invalid_realizations_handling():
    """
    Verify that the function correctly records indices of realizations that
    fail to become connected when the cutoff budget is intentionally too
    restrictive.
    """
    # Use a tiny initial factor and a max_factor that is deliberately low
    # so that many realizations will stay disconnected.
    success_rate, invalid = validate_connectivity_over_ensemble(
        num_realizations=20,
        n_atoms=30,
        factor=0.1,          # very small initial cutoff
        max_factor=0.2,      # restrict retries heavily
        step=0.05,
        seed=123,
    )
    # With such restrictive parameters we expect a low success rate.
    assert success_rate < 0.5
    # All failing realizations must be reported.
    assert len(invalid) == 20 - int(success_rate * 20)  # type: ignore