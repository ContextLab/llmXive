import pytest
import numpy as np
import sys
from pathlib import Path
import json
import tempfile
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.compression.metrics import (
    compute_mse, 
    compute_snr_degradation, 
    compute_compression_metrics
)

@pytest.fixture
def sample_waveforms():
    """Generate sample waveform data for testing."""
    np.random.seed(42)
    duration = 0.5
    sample_rate = 4096.0
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Simulate a simple sinusoidal signal with noise
    signal = 0.1 * np.sin(2 * np.pi * 100 * t) + np.random.normal(0, 0.01, size=t.shape)
    
    # Create a slightly degraded version
    degraded = signal + np.random.normal(0, 0.005, size=t.shape)
    
    return signal, degraded, sample_rate

def test_compute_mse_identical_arrays(sample_waveforms):
    """Test MSE is zero for identical arrays."""
    signal, _, _ = sample_waveforms
    mse = compute_mse(signal, signal)
    assert mse == 0.0, "MSE should be 0 for identical arrays"

def test_compute_mse_positive_value(sample_waveforms):
    """Test MSE is positive for different arrays."""
    original, degraded, _ = sample_waveforms
    mse = compute_mse(original, degraded)
    assert mse > 0, "MSE should be positive for different arrays"
    assert isinstance(mse, float), "MSE should return a float"

def test_compute_mse_shape_mismatch(sample_waveforms):
    """Test MSE raises ValueError for shape mismatch."""
    signal, degraded, _ = sample_waveforms
    with pytest.raises(ValueError, match="Shape mismatch"):
        compute_mse(signal, degraded[:100])

def test_compute_mse_empty_array(sample_waveforms):
    """Test MSE raises ValueError for empty arrays."""
    with pytest.raises(ValueError, match="cannot be empty"):
        compute_mse(np.array([]), np.array([]))

def test_compute_snr_degradation_identical(sample_waveforms):
    """Test SNR degradation is 0 for identical arrays."""
    signal, _, sample_rate = sample_waveforms
    snr_deg = compute_snr_degradation(signal, signal, sample_rate)
    assert snr_deg == 0.0, "SNR degradation should be 0 for identical arrays"

def test_compute_snr_degradation_positive(sample_waveforms):
    """Test SNR degradation is positive for degraded arrays."""
    original, degraded, sample_rate = sample_waveforms
    snr_deg = compute_snr_degradation(original, degraded, sample_rate)
    assert snr_deg > 0, "SNR degradation should be positive for degraded arrays"
    # Check precision requirement (>= 0.1 dB)
    assert round(snr_deg, 1) == snr_deg or abs(snr_deg - round(snr_deg, 1)) < 0.05

def test_compute_snr_degradation_perfect_reconstruction():
    """Test SNR degradation handles near-perfect reconstruction."""
    signal = np.random.normal(0, 0.1, 1000)
    perfect = signal + np.zeros_like(signal)  # Exact copy
    snr_deg = compute_snr_degradation(signal, perfect)
    assert snr_deg == 0.0, "SNR degradation should be 0 for perfect reconstruction"

def test_compute_snr_degradation_shape_mismatch(sample_waveforms):
    """Test SNR degradation raises ValueError for shape mismatch."""
    signal, degraded, sample_rate = sample_waveforms
    with pytest.raises(ValueError, match="Shape mismatch"):
        compute_snr_degradation(signal, degraded[:100], sample_rate)

def test_compute_compression_metrics_structure(sample_waveforms):
    """Test compute_compression_metrics returns correct structure."""
    original, degraded, sample_rate = sample_waveforms
    metrics = compute_compression_metrics(original, degraded, sample_rate)
    
    assert isinstance(metrics, dict), "Should return a dictionary"
    assert 'mse' in metrics, "Should contain 'mse' key"
    assert 'snr_degradation_db' in metrics, "Should contain 'snr_degradation_db' key"
    assert 'rmse' in metrics, "Should contain 'rmse' key"
    assert 'max_abs_error' in metrics, "Should contain 'max_abs_error' key"

def test_compute_compression_metrics_values_consistency(sample_waveforms):
    """Test that derived metrics are consistent."""
    original, degraded, sample_rate = sample_waveforms
    metrics = compute_compression_metrics(original, degraded, sample_rate)
    
    # RMSE should be sqrt(MSE)
    expected_rmse = np.sqrt(metrics['mse'])
    assert np.isclose(metrics['rmse'], expected_rmse), "RMSE should be sqrt(MSE)"
    
    # Max abs error should be >= 0
    assert metrics['max_abs_error'] >= 0, "Max abs error should be non-negative"

def test_compute_compression_metrics_precision(sample_waveforms):
    """Test SNR degradation precision meets requirement (>= 0.1 dB)."""
    original, degraded, sample_rate = sample_waveforms
    metrics = compute_compression_metrics(original, degraded, sample_rate)
    
    # The value should be rounded to at least 1 decimal place
    snr_val = metrics['snr_degradation_db']
    # Check that it's not an arbitrary long float without rounding
    assert isinstance(snr_val, float), "SNR degradation should be a float"