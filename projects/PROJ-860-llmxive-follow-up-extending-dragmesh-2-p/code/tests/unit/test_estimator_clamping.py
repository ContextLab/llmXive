"""
Unit tests for VirtualTactileEstimator FR-007 clamping logic.

Verifies that the estimator correctly bounds k_est values within [min_k, max_k]
as per FR-007 requirements.
"""
import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from estimator import VirtualTactileEstimator


class TestFR007ClampingLogic:
    """Test cases specifically for FR-007 bounded range clamping."""

    def test_clamping_respects_min_k(self):
        """Verify that k_est is clamped to min_k when calculation yields lower value."""
        estimator = VirtualTactileEstimator(window_size=1, min_k=0.5, max_k=10.0)
        
        # Create a scenario where raw calculation would be < min_k
        # k = |torque| / (|velocity| + epsilon)
        # If torque=0.0001, velocity=1.0, epsilon=1e-4: k ≈ 0.0001 / 1.0001 ≈ 0.0001
        # This is < min_k=0.5, so should be clamped
        result = estimator.update(torque=0.0001, velocity=1.0)
        
        assert result >= 0.5, f"Result {result} should be clamped to min_k=0.5"
        assert result == 0.5, f"Result {result} should equal min_k exactly when below threshold"

    def test_clamping_respects_max_k(self):
        """Verify that k_est is clamped to max_k when calculation yields higher value."""
        estimator = VirtualTactileEstimator(window_size=1, min_k=0.0, max_k=2.0)
        
        # Create a scenario where raw calculation would be > max_k
        # If torque=10.0, velocity=0.0001, epsilon=1e-4: k ≈ 10.0 / 0.0002 ≈ 50000
        # This is > max_k=2.0, so should be clamped
        result = estimator.update(torque=10.0, velocity=0.0001)
        
        assert result <= 2.0, f"Result {result} should be clamped to max_k=2.0"
        assert result == 2.0, f"Result {result} should equal max_k exactly when above threshold"

    def test_clamping_allows_normal_range(self):
        """Verify that values within [min_k, max_k] pass through unchanged."""
        estimator = VirtualTactileEstimator(window_size=1, min_k=0.0, max_k=100.0)
        
        # Create a scenario where raw calculation is within bounds
        # If torque=0.5, velocity=1.0, epsilon=1e-4: k ≈ 0.5 / 1.0001 ≈ 0.49995
        result = estimator.update(torque=0.5, velocity=1.0)
        
        expected = 0.5 / (1.0 + 1e-4)
        assert abs(result - expected) < 1e-6, f"Result {result} should equal expected {expected}"
        assert result >= 0.0 and result <= 100.0

    def test_clamping_with_moving_average(self):
        """Verify clamping works correctly after moving average smoothing."""
        estimator = VirtualTactileEstimator(window_size=3, min_k=1.0, max_k=5.0)
        
        # Feed values that would average to something outside bounds
        # First: very low (will be clamped to 1.0)
        estimator.update(torque=0.0001, velocity=1.0)  # raw ~0.0001 -> clamped 1.0
        # Second: very high (will be clamped to 5.0)
        estimator.update(torque=10.0, velocity=0.0001)  # raw ~50000 -> clamped 5.0
        # Third: very low again
        estimator.update(torque=0.0001, velocity=1.0)   # raw ~0.0001 -> clamped 1.0
        
        # Buffer now has [1.0, 5.0, 1.0] -> mean = 2.333...
        # This is within bounds, so no further clamping needed
        result = estimator.get_current_estimate()
        
        assert result is not None
        assert 1.0 <= result <= 5.0, f"Result {result} should be within [1.0, 5.0]"
        
        # Verify the mean calculation
        expected_mean = (1.0 + 5.0 + 1.0) / 3.0
        assert abs(result - expected_mean) < 1e-6, f"Result {result} should equal mean {expected_mean}"

    def test_clamping_boundary_precision(self):
        """Test clamping at exact boundary values."""
        estimator = VirtualTactileEstimator(window_size=1, min_k=2.0, max_k=8.0)
        
        # Test exactly at min_k
        # torque = 2.0 * (velocity + epsilon)
        # If velocity = 1.0: torque = 2.0 * 1.0001 = 2.0002
        result_min = estimator.update(torque=2.0002, velocity=1.0)
        assert abs(result_min - 2.0) < 1e-6, f"Result {result_min} should be exactly 2.0"
        
        # Test exactly at max_k
        # torque = 8.0 * (velocity + epsilon)
        # If velocity = 1.0: torque = 8.0 * 1.0001 = 8.0008
        result_max = estimator.update(torque=8.0008, velocity=1.0)
        assert abs(result_max - 8.0) < 1e-6, f"Result {result_max} should be exactly 8.0"

    def test_clamping_with_zero_velocity(self):
        """Verify clamping handles zero velocity (division by epsilon)."""
        estimator = VirtualTactileEstimator(window_size=1, min_k=0.0, max_k=1000.0)
        
        # Zero velocity with non-zero torque
        result = estimator.update(torque=1.0, velocity=0.0)
        
        # k = 1.0 / (0.0 + 1e-4) = 10000.0
        # Should be clamped to max_k=1000.0
        assert result == 1000.0, f"Result {result} should be clamped to max_k=1000.0"

    def test_clamping_configuration_validation(self):
        """Verify that invalid clamping configurations raise errors."""
        # min_k > max_k should raise ValueError
        with pytest.raises(ValueError):
            VirtualTactileEstimator(min_k=10.0, max_k=5.0)
        
        # min_k < 0 should raise ValueError
        with pytest.raises(ValueError):
            VirtualTactileEstimator(min_k=-1.0, max_k=10.0)

    def test_clamping_persistence_across_resets(self):
        """Verify clamping logic persists correctly after reset."""
        estimator = VirtualTactileEstimator(window_size=1, min_k=2.0, max_k=8.0)
        
        # Set a clamped value
        estimator.update(torque=100.0, velocity=0.0001)  # Should be clamped to 8.0
        first_result = estimator.get_current_estimate()
        assert first_result == 8.0
        
        # Reset
        estimator.reset()
        
        # Set another clamped value
        estimator.update(torque=0.0001, velocity=1.0)  # Should be clamped to 2.0
        second_result = estimator.get_current_estimate()
        assert second_result == 2.0

    def test_clamping_with_extreme_values(self):
        """Test clamping with extreme torque/velocity values."""
        estimator = VirtualTactileEstimator(window_size=1, min_k=0.1, max_k=50.0)
        
        # Very large torque
        result_large = estimator.update(torque=1e6, velocity=1.0)
        assert result_large == 50.0, f"Large torque should clamp to max_k"
        
        # Very small torque
        result_small = estimator.update(torque=1e-10, velocity=1.0)
        assert result_small == 0.1, f"Small torque should clamp to min_k"

    def test_clamping_preserves_finite_check(self):
        """Verify clamping doesn't interfere with finite number validation."""
        estimator = VirtualTactileEstimator(min_k=0.0, max_k=10.0)
        
        # Should raise ValueError for non-finite inputs
        with pytest.raises(ValueError):
            estimator.update(torque=float('inf'), velocity=1.0)
        
        with pytest.raises(ValueError):
            estimator.update(torque=1.0, velocity=float('nan'))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
