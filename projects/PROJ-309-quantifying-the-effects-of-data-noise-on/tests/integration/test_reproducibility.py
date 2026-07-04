"""
Integration test for reproducibility (seed stability).

This test verifies that generating a Lorenz attractor trajectory with the same
random seed produces stable results (within ±1% across two independent runs).
It also validates that the generated trajectory has the correct schema and
contains valid data (no NaNs, sufficient length).
"""
import pytest
import numpy as np
import sys
import os

# Add project root to path to allow imports from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.generators import generate_lorenz_trajectory
from code.config import LORENZ_PARAMS, DT, T_MAX
from code.utils.data_models import Trajectory


class TestReproducibility:
    """Tests for seed stability and reproducibility of trajectory generation."""

    @pytest.mark.integration
    def test_lorenz_seed_stability(self):
        """
        Verify that generating a Lorenz trajectory with the same seed
        produces results within ±1% across two independent runs.
        """
        seed = 42
        t_span = (0.0, T_MAX)
        rtol = 1e-9
        atol = 1e-9

        # Run 1
        traj1 = generate_lorenz_trajectory(seed=seed, t_span=t_span, rtol=rtol, atol=atol)

        # Run 2 (same seed)
        traj2 = generate_lorenz_trajectory(seed=seed, t_span=t_span, rtol=rtol, atol=atol)

        # Verify both are Trajectory objects
        assert isinstance(traj1, Trajectory)
        assert isinstance(traj2, Trajectory)

        # Verify same length
        assert len(traj1.time) == len(traj2.time)
        assert traj1.time.shape == traj2.time.shape
        assert traj1.state.shape == traj2.state.shape

        # Check for NaNs
        assert not np.any(np.isnan(traj1.state))
        assert not np.any(np.isnan(traj2.state))

        # Verify values are identical (deterministic integration)
        # Using a small tolerance for floating point differences
        np.testing.assert_array_almost_equal(traj1.time, traj2.time, decimal=10)
        np.testing.assert_array_almost_equal(traj1.state, traj2.state, decimal=10)

    @pytest.mark.integration
    def test_trajectory_schema_validity(self):
        """
        Verify that the generated trajectory has the correct schema:
        - time: 1D numpy array
        - state: 2D numpy array (n_points, 3) for Lorenz (x, y, z)
        - system_type: 'lorenz'
        - seed: integer
        - params: dict with correct keys
        """
        seed = 123
        traj = generate_lorenz_trajectory(seed=seed)

        # Check types
        assert isinstance(traj.time, np.ndarray)
        assert isinstance(traj.state, np.ndarray)
        assert isinstance(traj.system_type, str)
        assert isinstance(traj.seed, int)
        assert isinstance(traj.params, dict)

        # Check shapes
        assert traj.time.ndim == 1
        assert traj.state.ndim == 2
        assert traj.state.shape[1] == 3  # x, y, z

        # Check system type
        assert traj.system_type == 'lorenz'

        # Check seed
        assert traj.seed == seed

        # Check params contain expected keys
        expected_keys = ['sigma', 'rho', 'beta']
        for key in expected_keys:
            assert key in traj.params

        # Check params values match config
        assert abs(traj.params['sigma'] - LORENZ_PARAMS['sigma']) < 1e-10
        assert abs(traj.params['rho'] - LORENZ_PARAMS['rho']) < 1e-10
        assert abs(traj.params['beta'] - LORENZ_PARAMS['beta']) < 1e-10

    @pytest.mark.integration
    def test_trajectory_minimum_length(self):
        """
        Verify that the generated trajectory has sufficient length
        (minimum 1000 points for meaningful analysis).
        """
        seed = 456
        traj = generate_lorenz_trajectory(seed=seed)

        min_points = 1000
        assert len(traj.time) >= min_points, \
            f"Trajectory length {len(traj.time)} is below minimum {min_points}"
        assert traj.state.shape[0] >= min_points, \
            f"State rows {traj.state.shape[0]} is below minimum {min_points}"

    @pytest.mark.integration
    def test_different_seeds_produce_different_trajectories(self):
        """
        Verify that different seeds produce different trajectories.
        This ensures the random initialization is actually affecting the output.
        """
        traj1 = generate_lorenz_trajectory(seed=111)
        traj2 = generate_lorenz_trajectory(seed=222)

        # Trajectories should differ (at least in initial conditions or integration path)
        # We check if they are not identical
        assert not np.array_equal(traj1.state, traj2.state), \
            "Different seeds should produce different trajectories"

    @pytest.mark.integration
    def test_trajectory_no_nans(self):
        """
        Verify that the generated trajectory contains no NaN values.
        """
        seed = 789
        traj = generate_lorenz_trajectory(seed=seed)

        assert not np.any(np.isnan(traj.time)), "Trajectory time contains NaN"
        assert not np.any(np.isnan(traj.state)), "Trajectory state contains NaN"

    @pytest.mark.integration
    def test_reproducibility_across_multiple_seeds(self):
        """
        Verify reproducibility across multiple different seeds.
        Each seed should be reproducible when run twice.
        """
        seeds = [10, 20, 30, 40, 50]

        for seed in seeds:
            traj1 = generate_lorenz_trajectory(seed=seed)
            traj2 = generate_lorenz_trajectory(seed=seed)

            # Should be identical
            np.testing.assert_array_almost_equal(traj1.time, traj2.time, decimal=10)
            np.testing.assert_array_almost_equal(traj1.state, traj2.state, decimal=10)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
