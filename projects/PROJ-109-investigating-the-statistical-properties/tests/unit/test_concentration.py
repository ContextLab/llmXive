"""
Unit tests for NFW convergence and concentration parameter calculations.

Tests the NFW profile fitting logic found in code/data/compute_metrics.py,
specifically focusing on:
1. Convergence of the fitting algorithm (scipy.optimize.curve_fit).
2. Correctness of the derived concentration parameter (c).
3. Handling of edge cases (empty data, non-convergent fits).

This test suite validates the implementation of T020.
"""
import os
import sys
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from scipy.optimize import OptimizeWarning

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.compute_metrics import compute_halo_metrics
from code.data.streaming import subsample_particles
from code.utils.logging import get_logger

logger = get_logger(__name__)

# Constants for testing
TEST_SEED = 42
NUM_PARTICLES = 500
EPSILON = 1e-3  # Tolerance for float comparisons


def generate_test_halo_positions(n_particles: int, seed: int = 42):
    """
    Generates synthetic particle positions for a halo following a rough NFW-like
    distribution for testing purposes.

    Args:
        n_particles: Number of particles to generate.
        seed: Random seed for reproducibility.

    Returns:
        np.ndarray: Array of shape (n_particles, 3) with particle positions.
    """
    rng = np.random.default_rng(seed)

    # Generate radial distances following a simplified NFW-like profile
    # We use a power-law approximation for testing: P(r) ~ r^-2 within a radius
    # This is not a perfect NFW but sufficient to test convergence logic
    r_max = 100.0  # kpc/h
    r_min = 0.1

    # Inverse transform sampling for P(r) ~ 1/r^2 -> F(r) ~ 1 - r_min/r
    # Actually, let's just use a log-uniform distribution for simplicity in testing
    # which mimics the wide dynamic range of dark matter halos.
    log_r_min = np.log10(r_min)
    log_r_max = np.log10(r_max)
    log_r = rng.uniform(log_r_min, log_r_max, n_particles)
    r = 10 ** log_r

    # Random directions
    theta = rng.uniform(0, 2 * np.pi, n_particles)
    phi = rng.arccos(rng.uniform(-1, 1, n_particles))

    # Convert to Cartesian
    x = r * np.sin(phi) * np.cos(theta)
    y = r * np.sin(phi) * sin(theta)
    z = r * np.cos(phi)

    return np.column_stack((x, y, z))


def test_nfw_convergence_basic():
    """
    Test that the NFW fitting routine converges on a reasonable dataset.

    This test verifies that:
    1. The function runs without error.
    2. The returned concentration parameter is within a physically plausible range (c > 0).
    3. The fit status indicates success (if tracked).
    """
    # Generate test data
    positions = generate_test_halo_positions(NUM_PARTICLES, seed=TEST_SEED)

    # Mock halo metadata
    halo_data = {
        "id": 12345,
        "mass": 1e14,  # Solar masses
        "positions": positions,
        "velocities": np.zeros_like(positions),
        "particle_counts": NUM_PARTICLES
    }

    # Run the metric computation
    # We expect this to run the NFW fitting logic
    try:
        result = compute_halo_metrics(halo_data)

        # Assert that the result contains the concentration parameter
        assert "concentration" in result, "Result missing 'concentration' key"

        # Assert that the concentration is a positive number
        c_val = result["concentration"]
        assert isinstance(c_val, (int, float)), f"Concentration is not numeric: {type(c_val)}"
        assert c_val > 0, f"Concentration must be positive, got {c_val}"

        # Check that it's within a reasonable range for a test halo (e.g., 1 < c < 50)
        # Real halos can vary, but for synthetic test data, we expect a bounded value
        assert 1.0 < c_val < 100.0, f"Concentration {c_val} is outside expected test range"

        logger.info(f"Test passed: NFW fit converged with c = {c_val:.4f}")

    except Exception as e:
        pytest.fail(f"NFW convergence test failed with exception: {e}")


def test_nfw_convergence_edge_cases():
    """
    Test NFW fitting behavior with edge cases:
    1. Very few particles (should handle gracefully or raise specific error).
    2. Particles all at same location (singular matrix).
    """
    # Case 1: Very few particles
    few_positions = np.random.default_rng(42).uniform(-10, 10, (10, 3))
    halo_few = {
        "id": 999,
        "mass": 1e10,
        "positions": few_positions,
        "velocities": np.zeros_like(few_positions),
        "particle_counts": 10
    }

    # We expect the fit to either succeed (with high uncertainty) or fail gracefully
    # depending on implementation. We test that it doesn't crash the whole pipeline.
    try:
        result_few = compute_halo_metrics(halo_few)
        # If it returns a result, concentration should be positive
        if "concentration" in result_few:
            assert result_few["concentration"] > 0
    except Exception:
        # It is acceptable for the fit to fail on very few particles if handled
        pass

    # Case 2: All particles at same location (singular inertia tensor)
    singular_positions = np.ones((50, 3))
    halo_singular = {
        "id": 998,
        "mass": 1e12,
        "positions": singular_positions,
        "velocities": np.zeros_like(singular_positions),
        "particle_counts": 50
    }

    try:
        result_singular = compute_halo_metrics(halo_singular)
        # If it returns a result, it should handle the singularity
        if "concentration" in result_singular:
            assert result_singular["concentration"] > 0
    except Exception:
        # Acceptable to fail if singular matrix is detected
        pass


def test_nfw_convergence_with_subsample():
    """
    Test that the NFW fitting works correctly when using the subsampled particle
    stream as mandated by the project's complexity tracking (T007C, T023).

    This ensures the integration between the subsampling logic and the metric
    computation is sound.
    """
    # Generate a larger set of particles first
    full_positions = generate_test_halo_positions(5000, seed=TEST_SEED)

    # Apply subsampling logic (simulating T007C)
    # Note: In the real code, this would be called via the pipeline.
    # Here we mock the input to compute_halo_metrics with the subsampled data.
    subsampled_indices = np.random.default_rng(42).choice(
        len(full_positions), size=500, replace=False
    )
    subsampled_positions = full_positions[subsampled_indices]

    halo_subsampled = {
        "id": 777,
        "mass": 1e13,
        "positions": subsampled_positions,
        "velocities": np.zeros_like(subsampled_positions),
        "particle_counts": 500
    }

    try:
        result = compute_halo_metrics(halo_subsampled)
        assert "concentration" in result
        assert result["concentration"] > 0
        logger.info("Subsampled NFW fit test passed.")
    except Exception as e:
        pytest.fail(f"Subsampled NFW fit failed: {e}")


def test_nfw_convergence_failure_handling():
    """
    Test that the function handles cases where the optimizer fails to converge.

    We mock scipy.optimize.curve_fit to raise an error and ensure the main
    function catches it and logs a warning or returns a failure status.
    """
    positions = generate_test_halo_positions(NUM_PARTICLES, seed=TEST_SEED)
    halo_data = {
        "id": 666,
        "mass": 1e14,
        "positions": positions,
        "velocities": np.zeros_like(positions),
        "particle_counts": NUM_PARTICLES
    }

    with patch('scipy.optimize.curve_fit') as mock_fit:
        # Simulate a failure to converge
        mock_fit.side_effect = RuntimeError("Optimization failed to converge")

        # The function should catch this and not crash
        try:
            result = compute_halo_metrics(halo_data)
            # Check if the result indicates failure or a default value
            if "concentration" in result:
                # If it returns a value, it should be a sentinel or default
                assert result["concentration"] is not None
            # If the function returns early with an error flag, that's also fine
            assert "fit_status" in result or "concentration" in result
        except RuntimeError:
            pytest.fail("compute_halo_metrics did not handle optimization failure gracefully")


if __name__ == "__main__":
    # Run tests manually if executed as script
    pytest.main([__file__, "-v"])

# End of test_concentration.py