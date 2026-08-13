"""
Unit test for the hyperparameter sweep logic in ``code/training/sensitivity.py``.

The test verifies that the ``get_hyperparameter_grid`` function returns a list of
dictionaries covering the full Cartesian product of the expected message‑passing
step values (1, 2, 3) and the learning‑rate values defined by the implementation.

The test does **not** make any assumptions about the exact learning‑rate values,
only that they are present, numeric, and that the total number of grid entries
equals the product of the unique step values and unique learning‑rate values.
"""

import pytest

from training.sensitivity import get_hyperparameter_grid


def test_hyperparameter_grid_structure():
    """
    Ensure the hyperparameter grid is a list of dicts with the required keys and
    that it contains the full Cartesian product of the expected step values
    (1, 2, 3) and the learning‑rate values defined by the implementation.
    """
    grid = get_hyperparameter_grid()

    # The grid must be a list
    assert isinstance(grid, list), "Grid should be a list"

    # Each entry must be a dict containing at least the expected keys
    required_keys = {"msg_pass_steps", "learning_rate"}
    for entry in grid:
        assert isinstance(entry, dict), "Each grid entry must be a dict"
        missing = required_keys - entry.keys()
        assert not missing, f"Grid entry missing keys: {missing}"

    # Collect the unique values for each dimension
    steps = {entry["msg_pass_steps"] for entry in grid}
    learning_rates = {entry["learning_rate"] for entry in grid}

    # Expected message‑passing step values
    assert steps == {1, 2, 3}, f"Expected steps {{1,2,3}}, got {steps}"

    # There should be at least one learning‑rate defined
    assert learning_rates, "Learning‑rate set should not be empty"

    # Verify the Cartesian product size matches the grid length
    expected_len = len(steps) * len(learning_rates)
    assert len(grid) == expected_len, (
        f"Grid length {len(grid)} does not match expected Cartesian product size "
        f"{expected_len}"
    )

    # Optional sanity check: all combinations are present
    for step in steps:
        for lr in learning_rates:
            assert any(
                entry["msg_pass_steps"] == step and entry["learning_rate"] == lr
                for entry in grid
            ), f"Missing combination: step={step}, lr={lr}"

# The test can be run directly via pytest; no additional fixtures are required.