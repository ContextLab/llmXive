import pytest
from src.stats.simulator_metrics import (
    verify_noise_injection_target,
    validate_noisy_mode_simulation
)

class TestNoiseValidation:
    """Tests for T016b: Verify noise injection falls within 5-15% target range."""

    def test_noise_within_target_range(self):
        """Test that noise rates within 5-15% pass validation."""
        # Test lower bound
        verify_noise_injection_target(0.05)
        # Test upper bound
        verify_noise_injection_target(0.15)
        # Test middle
        verify_noise_injection_target(0.10)

    def test_noise_below_target_raises(self):
        """Test that noise rates below 5% raise AssertionError."""
        with pytest.raises(AssertionError) as exc_info:
            verify_noise_injection_target(0.02)
        
        assert "outside the target range" in str(exc_info.value)
        assert "0.02" in str(exc_info.value)

    def test_noise_above_target_raises(self):
        """Test that noise rates above 15% raise AssertionError."""
        with pytest.raises(AssertionError) as exc_info:
            verify_noise_injection_target(0.20)
        
        assert "outside the target range" in str(exc_info.value)
        assert "0.20" in str(exc_info.value)

    def test_tolerance_handling(self):
        """Test that tolerance allows slight deviations."""
        # 3% is below 5% but within tolerance (5-2=3)
        verify_noise_injection_target(0.03)
        # 17% is above 15% but within tolerance (15+2=17)
        verify_noise_injection_target(0.17)

    def test_tolerance_exceeded_raises(self):
        """Test that deviations beyond tolerance raise errors."""
        # 2% is below the effective lower bound (3%)
        with pytest.raises(AssertionError):
            verify_noise_injection_target(0.02)
        
        # 18% is above the effective upper bound (17%)
        with pytest.raises(AssertionError):
            verify_noise_injection_target(0.18)

    def test_validate_noisy_mode_success(self):
        """Test the full validation function with valid noise."""
        result = validate_noisy_mode_simulation(
            noise_injection_rate=0.10,
            ground_truth_error_rate=0.12
        )
        
        assert result.is_within_target_range is True
        assert result.noise_injection_rate == 0.10
        assert result.error_rate == 0.12

    def test_validate_noisy_mode_failure(self):
        """Test that the validation function raises on invalid noise."""
        with pytest.raises(AssertionError):
            validate_noisy_mode_simulation(
                noise_injection_rate=0.25,
                ground_truth_error_rate=0.30
            )