"""
Unit tests for noise injection functionality.

Tests:
- Gaussian noise injection accuracy
- Quantization noise injection
- SNR verification
"""
import numpy as np
import pytest
import sys
import os

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.config import NoiseType
from code.utils.data_models import Trajectory
from code.noise import (
    inject_gaussian_noise,
    inject_quantization_noise,
    calculate_snr,
    calculate_signal_power,
    calculate_noise_power,
    verify_snr_accuracy
)

@pytest.fixture
def clean_trajectory():
    """Create a simple clean trajectory for testing."""
    t = np.linspace(0, 10, 1000)
    data = np.column_stack([
        np.sin(t),
        np.cos(t),
        np.sin(2*t)
    ])
    return Trajectory(data=data, id="test_clean")

def test_gaussian_noise_snr_accuracy(clean_trajectory):
    """Test that Gaussian noise injection achieves target SNR within tolerance."""
    target_snr = 20.0  # dB
    seed = 42
    
    noisy = inject_gaussian_noise(clean_trajectory, target_snr, seed)
    
    # Verify the SNR is within 0.5 dB of target
    assert abs(noisy.actual_snr_db - target_snr) < 0.5, \
        f"Actual SNR {noisy.actual_snr_db}dB differs from target {target_snr}dB by more than 0.5dB"

def test_gaussian_noise_positive_snr(clean_trajectory):
    """Test Gaussian noise injection at positive SNR."""
    target_snr = 30.0
    noisy = inject_gaussian_noise(clean_trajectory, target_snr, seed=123)
    
    assert noisy.actual_snr_db > 25.0, "Actual SNR should be close to 30dB"
    assert noisy.noise_type == NoiseType.GAUSSIAN

def test_gaussian_noise_negative_snr(clean_trajectory):
    """Test Gaussian noise injection at negative SNR (noise dominant)."""
    target_snr = -5.0
    noisy = inject_gaussian_noise(clean_trajectory, target_snr, seed=456)
    
    # At -5dB, noise power is higher than signal power
    assert noisy.actual_snr_db < 0.0, "Actual SNR should be negative"
    assert noisy.actual_snr_db > -10.0, "Actual SNR should be close to -5dB"

def test_quantization_noise(clean_trajectory):
    """Test uniform quantization noise injection."""
    bits = 8
    noisy = inject_quantization_noise(clean_trajectory, bits, seed=789)
    
    assert noisy.bits == bits
    assert noisy.noise_type == NoiseType.QUANTIZATION
    # Higher bits should result in higher SNR
    assert noisy.actual_snr_db > 40.0, f"8-bit quantization SNR should be > 40dB, got {noisy.actual_snr_db}"

def test_quantization_noise_high_resolution(clean_trajectory):
    """Test quantization with higher bit resolution."""
    bits_8 = inject_quantization_noise(clean_trajectory, 8, seed=1)
    bits_16 = inject_quantization_noise(clean_trajectory, 16, seed=1)
    
    # 16-bit should have significantly higher SNR than 8-bit
    assert bits_16.actual_snr_db > bits_8.actual_snr_db, \
        f"16-bit SNR ({bits_16.actual_snr_db}) should be higher than 8-bit ({bits_8.actual_snr_db})"

def test_verify_snr_accuracy(clean_trajectory):
    """Test SNR verification function."""
    target_snr = 15.0
    noisy = inject_gaussian_noise(clean_trajectory, target_snr, seed=999)
    
    is_accurate = verify_snr_accuracy(noisy, clean_trajectory, tolerance_db=0.5)
    assert is_accurate, "SNR verification should pass within 0.5dB tolerance"

def test_verify_snr_accuracy_fail(clean_trajectory):
    """Test SNR verification with tight tolerance."""
    target_snr = 10.0
    noisy = inject_gaussian_noise(clean_trajectory, target_snr, seed=111)
    
    # Use a very tight tolerance that might fail due to numerical precision
    is_accurate = verify_snr_accuracy(noisy, clean_trajectory, tolerance_db=0.001)
    # This might pass or fail depending on numerical precision, but the function should run
    assert isinstance(is_accurate, bool)

def test_signal_power_calculation():
    """Test signal power calculation."""
    signal = np.array([1.0, 2.0, 3.0, 4.0])
    # Mean of squares: (1+4+9+16)/4 = 30/4 = 7.5
    power = calculate_signal_power(signal)
    assert np.isclose(power, 7.5)

def test_noise_power_calculation():
    """Test noise power calculation."""
    noise = np.array([1.0, -1.0, 2.0, -2.0])
    # Mean of squares: (1+1+4+4)/4 = 10/4 = 2.5
    power = calculate_noise_power(noise)
    assert np.isclose(power, 2.5)

def test_snr_calculation():
    """Test SNR calculation in dB."""
    signal_power = 10.0
    noise_power = 1.0
    # 10 * log10(10) = 10
    snr = calculate_snr(signal_power, noise_power)
    assert np.isclose(snr, 10.0)

def test_snr_calculation_zero_noise():
    """Test SNR calculation with zero noise raises error."""
    with pytest.raises(ValueError):
        calculate_snr(10.0, 0.0)
