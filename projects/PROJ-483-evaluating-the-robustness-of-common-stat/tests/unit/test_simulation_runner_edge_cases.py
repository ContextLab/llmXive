"""
Unit tests for edge cases in the simulation runner.

This test module covers:
- Correct output shape and type for the vectorized t‑test helper.
- Handling of invalid group assignments (e.g., all samples in one group).
- Behaviour when the number of samples is extremely small (N < 10).

The tests rely only on the public API exported by
`code/simulation_runner.py` (imported as `simulation_runner`).
They are deliberately lightweight and deterministic – a fixed random
seed is used for reproducibility.
"""

import numpy as np
import pytest

# The project adds the repository root to PYTHONPATH, so we can import
# directly from the module name without the ``code.`` prefix.
from simulation_runner import (
    _vectorized_t_test,
    SimulationError,
)

@pytest.fixture(scope="module")
def rng():
    """A deterministic random number generator for the test suite."""
    return np.random.default_rng(seed=42)

def test_vectorized_t_test_output_shape(rng):
    """
    Verify that the vectorized t‑test returns an array of p‑values
    whose length matches the number of replications supplied in ``data``.
    """
    n_replications = 20
    n_samples = 30

    # Generate synthetic normal data for two groups.
    # Group 0: first half, Group 1: second half.
    data = rng.normal(loc=0.0, scale=1.0, size=(n_replications, n_samples))

    # Create a deterministic group assignment: first 15 samples = 0,
    # last 15 samples = 1.
    group_indices = np.array([0] * (n_samples // 2) + [1] * (n_samples - n_samples // 2))

    pvals = _vectorized_t_test(data, group_indices)

    # The function must return a 1‑D NumPy array with ``n_replications`` entries.
    assert isinstance(pvals, np.ndarray), "Returned object is not a NumPy array"
    assert pvals.shape == (n_replications,), (
        f"Expected shape {(n_replications,)}, got {pvals.shape}"
    )
    # All p‑values must be between 0 and 1.
    assert np.all((pvals >= 0) & (pvals <= 1)), "P‑values fall outside [0, 1]"

def test_vectorized_t_test_invalid_groups(rng):
    """
    The helper should raise a ``SimulationError`` when the group vector
    does not contain at least two distinct labels (i.e., no between‑group
    variation). This mirrors the edge‑case handling required for null
    hypothesis construction on degenerate data.
    """
    n_replications = 5
    n_samples = 10

    data = rng.normal(size=(n_replications, n_samples))

    # All samples assigned to the same group (invalid).
    group_indices = np.zeros(n_samples, dtype=int)

    with pytest.raises(SimulationError):
        _vectorized_t_test(data, group_indices)

def test_vectorized_t_test_small_n(rng):
    """
    Ensure the function behaves sensibly when the number of samples
    per replication is very small (e.g., N = 3). The implementation
    should still compute a t‑test (although the statistical power is
    low) and return a valid p‑value array.
    """
    n_replications = 8
    n_samples = 3  # Very small sample size

    data = rng.normal(loc=0.0, scale=1.0, size=(n_replications, n_samples))

    # Assign groups such that we have at least one observation per group.
    # For N=3 we can use groups [0, 1, 0].
    group_indices = np.array([0, 1, 0])

    pvals = _vectorized_t_test(data, group_indices)

    assert isinstance(pvals, np.ndarray)
    assert pvals.shape == (n_replications,)
    assert np.all((pvals >= 0) & (pvals <= 1)), "P‑values out of bounds for small N"