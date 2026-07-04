"""
Unit tests for noise injection and SNR calculation in code/noise.py.

This module verifies:
1. SNR calculation accuracy against target levels (±0.5dB tolerance)
2. Correctness of signal and noise power calculations
3. Proper behavior of noise injection functions
"""

import pytest
import numpy as np
from scipy import signal as scipy_signal

# Import the functions being tested from the project's noise module
from code.noise import (
    calculate_signal_power,
    calculate_noise_power,
    calculate_snr,
    inject_gaussian_noise,
    inject_quantization_noise
)
from code.config import NoiseType, get_snr_levels
from code.utils.data_models import Trajectory

# Test fixtures and constants
TEST_SEED = 42
TEST_DURATION = 10.0
TEST_DT = 0.01
TEST_SIGNAL_LENGTH = int(TEST_DURATION / TEST_DT)

@pytest.fixture
def clean_signal():
    """Generate a deterministic clean signal for testing."""
    np.random.seed(TEST_SEED)
    t = np.arange(0, TEST_DURATION, TEST_DT)
    # Use a mix of sinusoids to create a non-trivial signal
    signal = np.sin(2 * np.pi * 10 * t) + 0.5 * np.sin(2 * np.pi * 25 * t)
    return signal

@pytest.fixture
def trajectory_data(clean_signal):
    """Create a Trajectory object with clean signal data."""
    return Trajectory(
        system_type="test",
        seed=TEST_SEED,
        time=np.arange(0, TEST_DURATION, TEST_DT),
        x=clean_signal,
        y=np.zeros_like(clean_signal),
        z=np.zeros_like(clean_signal)
    )

class TestSignalPowerCalculation:
    """Tests for calculate_signal_power function."""
    
    def test_signal_power_positive_values(self, clean_signal):
        """Signal power should always be positive."""
        power = calculate_signal_power(clean_signal)
        assert power > 0, "Signal power must be positive"
    
    def test_signal_power_consistency(self, clean_signal):
        """Signal power should be consistent across calls."""
        power1 = calculate_signal_power(clean_signal)
        power2 = calculate_signal_power(clean_signal)
        assert np.isclose(power1, power2), "Signal power should be deterministic"
    
    def test_signal_power_calculation_method(self, clean_signal):
        """Verify signal power is calculated as mean of squared values."""
        expected_power = np.mean(clean_signal ** 2)
        calculated_power = calculate_signal_power(clean_signal)
        assert np.isclose(calculated_power, expected_power), \
            f"Signal power calculation mismatch: {calculated_power} vs {expected_power}"

class TestNoisePowerCalculation:
    """Tests for calculate_noise_power function."""
    
    def test_noise_power_positive_values(self, clean_signal):
        """Noise power should always be positive."""
        noise = np.random.randn(TEST_SIGNAL_LENGTH)
        power = calculate_noise_power(noise)
        assert power > 0, "Noise power must be positive"
    
    def test_noise_power_calculation_method(self, clean_signal):
        """Verify noise power is calculated as mean of squared values."""
        noise = np.random.randn(TEST_SIGNAL_LENGTH)
        expected_power = np.mean(noise ** 2)
        calculated_power = calculate_noise_power(noise)
        assert np.isclose(calculated_power, expected_power), \
            f"Noise power calculation mismatch: {calculated_power} vs {expected_power}"

class TestSNRCalculation:
    """Tests for calculate_snr function and SNR accuracy."""
    
    def test_snr_formula_correctness(self):
        """Verify SNR formula: 10 * log10(P_signal / P_noise)."""
        signal_power = 10.0
        noise_power = 1.0
        expected_snr = 10 * np.log10(signal_power / noise_power)
        calculated_snr = calculate_snr(signal_power, noise_power)
        assert np.isclose(calculated_snr, expected_snr), \
            f"SNR formula incorrect: {calculated_snr} vs {expected_snr}"
    
    def test_snr_zero_noise(self):
        """SNR should approach infinity when noise power is zero."""
        signal_power = 10.0
        noise_power = 1e-15  # Effectively zero
        calculated_snr = calculate_snr(signal_power, noise_power)
        assert calculated_snr > 100, "SNR should be very high for near-zero noise"
    
    def test_snr_across_target_levels(self, clean_signal):
        """Test that injected noise achieves target SNR within ±0.5dB tolerance."""
        target_snrs = get_snr_levels()
        
        for target_snr in target_snrs:
            # Inject Gaussian noise at the target SNR
            noisy_signal = inject_gaussian_noise(
                clean_signal, 
                target_snr=target_snr,
                seed=TEST_SEED
            )
            
            # Calculate actual SNR
            signal_power = calculate_signal_power(clean_signal)
            noise = noisy_signal - clean_signal
            noise_power = calculate_noise_power(noise)
            actual_snr = calculate_snr(signal_power, noise_power)
            
            # Verify within tolerance
            tolerance = 0.5
            assert abs(actual_snr - target_snr) <= tolerance, \
                f"SNR accuracy failed for target {target_snr}dB: " \
                f"actual={actual_snr:.2f}dB, error={abs(actual_snr - target_snr):.2f}dB"
    
    def test_snr_negative_levels(self):
        """Test SNR calculation at negative dB levels."""
        target_snr = -5.0
        signal = np.random.randn(1000) * 10
        signal_power = calculate_signal_power(signal)
        
        # Calculate required noise power for target SNR
        # SNR = 10 * log10(P_signal / P_noise)
        # P_noise = P_signal / 10^(SNR/10)
        required_noise_power = signal_power / (10 ** (target_snr / 10))
        
        # Generate noise with the required power
        noise_std = np.sqrt(required_noise_power)
        noise = np.random.randn(len(signal)) * noise_std
        
        # Verify the SNR
        actual_snr = calculate_snr(signal_power, calculate_noise_power(noise))
        assert abs(actual_snr - target_snr) <= 0.5, \
            f"Negative SNR test failed: target={target_snr}dB, actual={actual_snr:.2f}dB"

class TestGaussianNoiseInjection:
    """Tests for inject_gaussian_noise function."""
    
    def test_noise_addition(self, clean_signal):
        """Verify that noise is actually added to the signal."""
        noisy_signal = inject_gaussian_noise(clean_signal, target_snr=20.0, seed=TEST_SEED)
        assert not np.array_equal(clean_signal, noisy_signal), \
            "Noisy signal should differ from clean signal"
    
    def test_noise_preserves_signal_length(self, clean_signal):
        """Noisy signal should have the same length as clean signal."""
        noisy_signal = inject_gaussian_noise(clean_signal, target_snr=20.0, seed=TEST_SEED)
        assert len(noisy_signal) == len(clean_signal), \
            "Noisy signal length should match clean signal length"
    
    def test_noise_distribution_properties(self, clean_signal):
        """Verify that injected noise follows Gaussian distribution."""
        noisy_signal = inject_gaussian_noise(clean_signal, target_snr=10.0, seed=TEST_SEED)
        noise = noisy_signal - clean_signal
        
        # Check that noise has approximately zero mean
        assert np.abs(np.mean(noise)) < 0.1, "Noise mean should be close to zero"
        
        # Check that noise has finite variance
        assert np.isfinite(np.var(noise)), "Noise variance should be finite"
    
    def test_deterministic_with_seed(self, clean_signal):
        """Verify deterministic behavior with fixed seed."""
        noisy1 = inject_gaussian_noise(clean_signal, target_snr=15.0, seed=TEST_SEED)
        noisy2 = inject_gaussian_noise(clean_signal, target_snr=15.0, seed=TEST_SEED)
        assert np.array_equal(noisy1, noisy2), \
            "Same seed should produce identical noisy signals"

class TestQuantizationNoiseInjection:
    """Tests for inject_quantization_noise function."""
    
    def test_quantization_levels(self, clean_signal):
        """Verify quantization creates discrete levels."""
        noisy_signal = inject_quantization_noise(clean_signal, bits=4)
        # With 4 bits, we should have at most 16 distinct levels
        unique_levels = len(np.unique(noisy_signal))
        assert unique_levels <= 16, f"Quantization should create ≤16 levels, got {unique_levels}"
    
    def test_quantization_preserves_range(self, clean_signal):
        """Quantization should preserve the approximate signal range."""
        noisy_signal = inject_quantization_noise(clean_signal, bits=8)
        signal_range = np.max(clean_signal) - np.min(clean_signal)
        noisy_range = np.max(noisy_signal) - np.min(noisy_signal)
        # Allow some tolerance for quantization effects
        assert abs(noisy_range - signal_range) / signal_range < 0.1, \
            "Quantized signal range should be close to original"
    
    def test_quantization_bit_resolutions(self, clean_signal):
        """Test various bit resolutions."""
        for bits in [4, 8, 12, 16]:
            noisy_signal = inject_quantization_noise(clean_signal, bits=bits)
            unique_levels = len(np.unique(noisy_signal))
            max_levels = 2 ** bits
            assert unique_levels <= max_levels, \
                f"Quantization with {bits} bits should have ≤{max_levels} levels, got {unique_levels}"
    
    def test_quantization_deterministic(self, clean_signal):
        """Verify deterministic behavior for quantization."""
        noisy1 = inject_quantization_noise(clean_signal, bits=8)
        noisy2 = inject_quantization_noise(clean_signal, bits=8)
        assert np.array_equal(noisy1, noisy2), \
            "Quantization should be deterministic"

class TestIntegrationWithTrajectory:
    """Integration tests using Trajectory objects."""
    
    def test_trajectory_noise_injection(self, trajectory_data):
        """Test noise injection on a full trajectory object."""
        from code.noise import inject_gaussian_noise_to_trajectory
        
        # This test assumes the function exists or will be added
        # For now, test the component functions with trajectory data
        signal = trajectory_data.x
        noisy_signal = inject_gaussian_noise(signal, target_snr=25.0, seed=TEST_SEED)
        
        # Verify the noisy signal maintains trajectory properties
        assert len(noisy_signal) == len(trajectory_data.time), \
            "Noisy signal should match trajectory time length"
        
        # Verify SNR accuracy
        signal_power = calculate_signal_power(signal)
        noise_power = calculate_noise_power(noisy_signal - signal)
        actual_snr = calculate_snr(signal_power, noise_power)
        assert abs(actual_snr - 25.0) <= 0.5, \
            f"Trajectory noise injection failed: target=25dB, actual={actual_snr:.2f}dB"

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_signal(self):
        """Handle empty signal gracefully."""
        empty_signal = np.array([])
        with pytest.raises((ValueError, IndexError)):
            calculate_signal_power(empty_signal)
    
    def test_constant_signal(self):
        """Test with constant signal (zero variance)."""
        constant_signal = np.ones(100) * 5.0
        power = calculate_signal_power(constant_signal)
        assert power == 25.0, "Power of constant signal should be square of value"
    
    def test_very_small_signal(self):
        """Test with very small signal values."""
        tiny_signal = np.random.randn(100) * 1e-10
        power = calculate_signal_power(tiny_signal)
        assert power > 0, "Power should be positive even for tiny signals"
        assert np.isfinite(power), "Power should be finite"
    
    def test_very_large_signal(self):
        """Test with very large signal values."""
        huge_signal = np.random.randn(100) * 1e10
        power = calculate_signal_power(huge_signal)
        assert power > 0, "Power should be positive for large signals"
        assert np.isfinite(power), "Power should be finite for large signals"

class TestPerformance:
    """Basic performance tests."""
    
    def test_large_signal_handling(self):
        """Test with large signal to ensure reasonable performance."""
        large_signal = np.random.randn(100000)
        
        import time
        start = time.time()
        _ = calculate_signal_power(large_signal)
        _ = calculate_noise_power(large_signal)
        _ = inject_gaussian_noise(large_signal, target_snr=20.0, seed=TEST_SEED)
        elapsed = time.time() - start
        
        # Should complete in reasonable time (< 5 seconds for 100k points)
        assert elapsed < 5.0, f"Performance issue: {elapsed:.2f}s for large signal"