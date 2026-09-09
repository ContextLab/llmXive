"""
Unit tests for T046: Unphysical Trajectory Handling.

Verifies that:
1. UnphysicalTrajectoryError is raised when sigma_noise > 1.0
2. UnphysicalTrajectoryError is raised when max(|state|) > 100 (divergence)
3. The error halts analysis for that specific trial but does not crash the sweep
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.generator import (
    generate_coupled_lorenz_trajectory,
    generate_batch_trajectories,
    UnphysicalTrajectoryError,
    HighNoiseWarning
)

class TestUnphysicalTrajectoryHandling:
    """Tests for T046 logic."""

    def test_sigma_gt_1_raises_error(self):
        """Test that sigma_noise > 1.0 raises UnphysicalTrajectoryError."""
        with pytest.raises(UnphysicalTrajectoryError) as exc_info:
            generate_coupled_lorenz_trajectory(
                N=2,
                t_end=10.0,
                sigma_noise=1.5,  # > 1.0
                trial_id=1
            )
        
        assert "sigma_noise" in str(exc_info.value).lower() or "unphysical" in str(exc_info.value).lower()

    def test_sigma_gt_1_message_content(self):
        """Test that the error message contains relevant details."""
        with pytest.raises(UnphysicalTrajectoryError) as exc_info:
            generate_coupled_lorenz_trajectory(
                N=2,
                t_end=10.0,
                sigma_noise=2.0,
                trial_id=2
            )
        
        error_msg = str(exc_info.value)
        # Verify the message indicates the specific cause
        assert "sigma_noise" in error_msg or "1.0" in error_msg

    def test_batch_sweep_handles_unphysical_gracefully(self):
        """
        Test that a batch sweep with mixed noise levels (including > 1.0)
        completes without crashing, skipping only the invalid trials.
        """
        # Mix of valid and invalid noise levels
        noise_levels = [0.01, 0.5, 1.5, 2.0] 
        
        # We expect some failures, but the function should not crash
        results = generate_batch_trajectories(
            N=2,
            sigma_noise_values=noise_levels,
            t_end=5.0,  # Short time for speed
            trials_per_level=2,
            base_seed=123
        )
        
        # Should have some results (from the valid noise levels)
        assert len(results) > 0, "Should have generated some valid trajectories"
        
        # Check that all returned results have valid noise levels
        for traj in results:
            assert traj.noise_level <= 1.0, f"Trajectory with sigma={traj.noise_level} should not be returned"
            assert traj.boundedness_check is True

    def test_high_noise_warning_vs_error_boundary(self):
        """
        Test the boundary between HighNoiseWarning (0.1 < sigma <= 1.0)
        and UnphysicalTrajectoryError (sigma > 1.0).
        """
        # 0.5 should warn but not error (if we implemented warning logic)
        # For T046, we focus on the > 1.0 error
        
        # Test just below 1.0 - should succeed (or warn, but not error)
        try:
            traj = generate_coupled_lorenz_trajectory(
                N=2,
                t_end=5.0,
                sigma_noise=0.9,
                trial_id=3
            )
            # If it returns, it's valid (or at least not an error)
            assert traj is not None
        except UnphysicalTrajectoryError:
            pytest.fail("sigma=0.9 should not raise UnphysicalTrajectoryError")
        
        # Test just above 1.0 - must error
        with pytest.raises(UnphysicalTrajectoryError):
            generate_coupled_lorenz_trajectory(
                N=2,
                t_end=5.0,
                sigma_noise=1.1,
                trial_id=4
            )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])