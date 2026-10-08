"""
Tests for sensitivity analysis and surrogate validation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

from sensitivity import (
    generate_phase_randomized_surrogate,
    compute_entropy_on_surrogates,
    run_surrogate_validation
)
from entropy import compute_multiscale_entropy

@pytest.fixture
def sample_time_series():
    """Generate a sample time series for testing."""
    np.random.seed(42)
    # Create a time series with some structure
    t = np.linspace(0, 10, 500)
    signal = np.sin(2 * np.pi * t) + 0.5 * np.sin(4 * np.pi * t) + np.random.normal(0, 0.1, 500)
    return signal

@pytest.fixture
def sample_surrogate_data():
    """Generate sample surrogate data for testing."""
    np.random.seed(42)
    ts = np.sin(2 * np.pi * np.linspace(0, 10, 500)) + np.random.normal(0, 0.1, 500)
    surrogate1 = generate_phase_randomized_surrogate(ts)
    surrogate2 = generate_phase_randomized_surrogate(ts)
    
    return {
        'subj_001': [surrogate1, surrogate2],
        'subj_002': [generate_phase_randomized_surrogate(ts), generate_phase_randomized_surrogate(ts)]
    }

def test_generate_phase_randomized_surrogate_preserves_spectrum(sample_time_series):
    """Test that surrogate preserves power spectrum."""
    surrogate = generate_phase_randomized_surrogate(sample_time_series)
    
    # Compute power spectra
    fft_orig = np.abs(np.fft.fft(sample_time_series))
    fft_surr = np.abs(np.fft.fft(surrogate))
    
    # Power spectrum should be identical (up to numerical precision)
    np.testing.assert_array_almost_equal(fft_orig, fft_surr, decimal=10)
    
    # But the time series should be different
    assert not np.allclose(sample_time_series, surrogate)

def test_generate_phase_randomized_surrogate_mean_variance(sample_time_series):
    """Test that surrogate preserves mean and variance."""
    surrogate = generate_phase_randomized_surrogate(sample_time_series)
    
    np.testing.assert_almost_equal(np.mean(sample_time_series), np.mean(surrogate), decimal=5)
    np.testing.assert_almost_equal(np.var(sample_time_series), np.var(surrogate), decimal=5)

def test_compute_entropy_on_surrogates(sample_surrogate_data):
    """Test entropy computation on surrogate data."""
    result_df = compute_entropy_on_surrogates(
        sample_surrogate_data,
        m=2,
        r=0.2,
        scales=range(1, 6)  # Use fewer scales for speed
    )
    
    # Check that we got results
    assert len(result_df) > 0
    assert 'subject_id' in result_df.columns
    assert 'surrogate_idx' in result_df.columns
    assert 'entropy_value' in result_df.columns
    
    # Check that entropy values are reasonable (positive, finite)
    assert all(result_df['entropy_value'] > 0)
    assert all(np.isfinite(result_df['entropy_value']))

def test_run_surrogate_validation(tmp_path):
    """Test the full surrogate validation pipeline."""
    # Create a mock real entropy file
    real_entropy_df = pd.DataFrame({
        'subject_id': ['subj_001', 'subj_002'],
        'entropy_value': [1.5, 1.8]
    })
    real_path = tmp_path / "entropy_metrics.csv"
    real_entropy_df.to_csv(real_path, index=False)
    
    output_path = tmp_path / "surrogate_results.csv"
    
    # Run validation (with minimal surrogates for speed)
    run_surrogate_validation(
        real_entropy_path=str(real_path),
        surrogate_output_path=str(output_path),
        n_surrogates=2,
        m=2,
        r=0.2,
        scales=range(1, 6)
    )
    
    # Check output file exists and has content
    assert output_path.exists()
    result_df = pd.read_csv(output_path)
    
    assert len(result_df) > 0
    assert 'subject_id' in result_df.columns
    assert 'entropy_value' in result_df.columns
    assert 'entropy_real_avg' in result_df.columns
    assert 'difference' in result_df.columns
    assert 'pass_flag' in result_df.columns
