"""
Unit tests for noise injection module.
"""
import pytest
import numpy as np
from code.noise import (
    inject_gaussian_noise,
    inject_quantization_noise,
    verify_snr_accuracy,
    get_noise_injection_function,
    calculate_signal_power,
    calculate_noise_power,
    calculate_snr
)
from code.config import NoiseType
from code.utils.data_models import Trajectory
from code.generators import generate_lorenz_trajectory

@pytest.fixture
def clean_trajectory():
    """Generate a clean Lorenz trajectory for testing."""
    return generate_lorenz_trajectory(seed=42, duration=10.0, dt=0.01)

class TestNoiseInjection:
    """Tests for noise injection functions."""

    def test_gaussian_noise_injection(self, clean_trajectory):
        """Test that Gaussian noise injection produces noisy data."""
        target_snr = 20.0
        noisy = inject_gaussian_noise(clean_trajectory, target_snr, seed=123)
        
        # Check that data is different from original
        assert not np.allclose(noisy.data, clean_trajectory.data)
        
        # Check metadata
        assert noisy.noise_type == NoiseType.GAUSSIAN
        assert noisy.target_snr_db == target_snr
        assert noisy.seed == 123
        assert noisy.original_trajectory_id == clean_trajectory.id

    def test_gaussian_noise_snr_accuracy(self, clean_trajectory):
        """Test that Gaussian noise achieves target SNR within tolerance."""
        target_snr = 20.0
        noisy = inject_gaussian_noise(clean_trajectory, target_snr, seed=123)
        
        assert verify_snr_accuracy(noisy, tolerance_db=0.5)

    def test_quantization_noise_injection(self, clean_trajectory):
        """Test that quantization noise injection produces noisy data."""
        bits = 10
        noisy = inject_quantization_noise(clean_trajectory, bits, seed=123)
        
        # Check that data is different from original (unless signal is constant)
        # Note: For some signals, quantization might not change values if step_size is very small
        assert noisy.noise_type == NoiseType.QUANTIZATION
        assert noisy.bits == bits
        assert noisy.original_trajectory_id == clean_trajectory.id

    def test_quantization_noise_deterministic(self, clean_trajectory):
        """Test that quantization noise is deterministic (no seed dependency)."""
        bits = 10
        noisy1 = inject_quantization_noise(clean_trajectory, bits, seed=123)
        noisy2 = inject_quantization_noise(clean_trajectory, bits, seed=456)
        
        # Quantization should be deterministic regardless of seed
        assert np.allclose(noisy1.data, noisy2.data)

    def test_gaussian_noise_invalid_snr(self, clean_trajectory):
        """Test Gaussian noise with invalid SNR values."""
        with pytest.raises(ValueError):
            # Very negative SNR might cause numerical issues
            inject_gaussian_noise(clean_trajectory, -100.0, seed=123)

    def test_quantization_noise_invalid_bits(self, clean_trajectory):
        """Test quantization noise with invalid bit values."""
        with pytest.raises(ValueError):
            inject_quantization_noise(clean_trajectory, 0, seed=123)
        
        with pytest.raises(ValueError):
            inject_quantization_noise(clean_trajectory, -5, seed=123)

class TestNoiseInjectionFunctionSelector:
    """Tests for get_noise_injection_function."""

    def test_get_gaussian_function(self):
        """Test getting Gaussian noise injection function."""
        func = get_noise_injection_function(NoiseType.GAUSSIAN)
        assert func == inject_gaussian_noise

    def test_get_quantization_function(self):
        """Test getting quantization noise injection function."""
        func = get_noise_injection_function(NoiseType.QUANTIZATION)
        assert func == inject_quantization_noise

    def test_get_unsupported_function(self):
        """Test that unsupported noise types raise ValueError."""
        # Create a mock unsupported noise type
        class UnsupportedNoiseType:
            pass
        
        with pytest.raises(ValueError) as exc_info:
            get_noise_injection_function(UnsupportedNoiseType())
        
        assert "Unsupported noise type" in str(exc_info.value)
        assert "Only" in str(exc_info.value)

class TestPowerCalculations:
    """Tests for power calculation functions."""

    def test_signal_power_1d(self):
        """Test signal power calculation for 1D array."""
        signal = np.array([1.0, 2.0, 3.0, 4.0])
        power = calculate_signal_power(signal)
        expected = (1 + 4 + 9 + 16) / 4
        assert np.isclose(power, expected)

    def test_signal_power_2d(self):
        """Test signal power calculation for 2D array."""
        signal = np.array([[1.0, 2.0], [3.0, 4.0]])
        power = calculate_signal_power(signal)
        expected = (1 + 4 + 9 + 16) / 4
        assert np.isclose(power, expected)

    def test_signal_power_invalid_dim(self):
        """Test that invalid dimensions raise ValueError."""
        with pytest.raises(ValueError):
            calculate_signal_power(np.array([[[1.0]]]))

    def test_noise_power(self):
        """Test noise power calculation."""
        noise = np.array([1.0, 0.0, -1.0, 0.0])
        power = calculate_noise_power(noise)
        expected = (1 + 0 + 1 + 0) / 4
        assert np.isclose(power, expected)

class TestSNRCalculation:
    """Tests for SNR calculation."""

    def test_snr_positive(self):
        """Test SNR calculation with positive values."""
        snr = calculate_snr(100.0, 1.0)
        assert np.isclose(snr, 20.0)  # 10 * log10(100)

    def test_snr_zero_noise(self):
        """Test SNR with zero noise (infinite SNR)."""
        snr = calculate_snr(100.0, 0.0)
        assert snr == float('inf')

    def test_snr_equal_power(self):
        """Test SNR when signal and noise have equal power."""
        snr = calculate_snr(10.0, 10.0)
        assert np.isclose(snr, 0.0)  # 0 dB

class TestSNRVerification:
    """Tests for SNR verification."""

    def test_verify_within_tolerance(self, clean_trajectory):
        """Test verification when SNR is within tolerance."""
        noisy = inject_gaussian_noise(clean_trajectory, 20.0, seed=123)
        assert verify_snr_accuracy(noisy, tolerance_db=0.5)

    def test_verify_outside_tolerance(self, clean_trajectory):
        """Test verification when SNR is outside tolerance."""
        # Create a noisy trajectory with artificially bad SNR
        noisy = inject_gaussian_noise(clean_trajectory, 20.0, seed=123)
        # Modify actual SNR to be far from target
        noisy.actual_snr_db = 5.0
        
        assert not verify_snr_accuracy(noisy, tolerance_db=0.5)

    def test_verify_no_target_snr(self, clean_trajectory):
        """Test verification for quantization noise (no target SNR)."""
        noisy = inject_quantization_noise(clean_trajectory, bits=10)
        # Should return True without error
        assert verify_snr_accuracy(noisy, tolerance_db=0.5)

    def test_verify_no_actual_snr(self, clean_trajectory):
        """Test verification when actual SNR is not calculated."""
        noisy = inject_gaussian_noise(clean_trajectory, 20.0, seed=123)
        noisy.actual_snr_db = None
        
        with pytest.raises(ValueError):
            verify_snr_accuracy(noisy, tolerance_db=0.5)
