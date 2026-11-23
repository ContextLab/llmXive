"""
Unit tests for src.data.metrics module.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
import tempfile
from pathlib import Path
import sys
import os

# Add src to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.metrics import (
    compute_acf_lag, 
    compute_dfa_hurst, 
    compute_spectral_peak_ratio, 
    compute_all_metrics, 
    compute_metrics_for_dataset,
    MetricsError
)

# Fixtures for test data
@pytest.fixture
def white_noise_series():
    """Generate a white noise series (H ~ 0.5, ACF ~ 0)."""
    np.random.seed(42)
    return np.random.normal(0, 1, 1000)

@pytest.fixture
def persistent_series():
    """Generate a persistent series (H > 0.5, positive ACF)."""
    np.random.seed(42)
    # Create a series with persistence using cumulative sum of noise
    noise = np.random.normal(0, 1, 1000)
    return np.cumsum(noise)

@pytest.fixture
def periodic_series():
    """Generate a series with strong periodicity."""
    np.random.seed(42)
    t = np.linspace(0, 100, 1000)
    return np.sin(t) + np.random.normal(0, 0.1, 1000)

@pytest.fixture
def short_series():
    """Generate a series too short for metrics."""
    return np.array([1.0, 2.0, 3.0])

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary directory for test data files."""
    return tmp_path

class TestACF:
    def test_acf_lag_0_is_one(self, white_noise_series):
        """ACF at lag 0 should always be 1.0."""
        acf = compute_acf_lag(white_noise_series, max_lag=5)
        assert acf[0] == 1.0

    def test_acf_white_noise_near_zero(self, white_noise_series):
        """ACF for white noise should be close to 0 for lags > 0."""
        acf = compute_acf_lag(white_noise_series, max_lag=10)
        for lag in range(1, 11):
            # Allow some tolerance due to randomness
            assert abs(acf[lag]) < 0.1, f"ACF at lag {lag} is too high: {acf[lag]}"

    def test_acf_persistent_positive(self, persistent_series):
        """ACF for persistent series should be positive."""
        acf = compute_acf_lag(persistent_series, max_lag=5)
        # Lag 1 should be significantly positive
        assert acf[1] > 0.5, f"Lag 1 ACF too low: {acf[1]}"

    def test_acf_short_series_raises(self, short_series):
        """ACF should raise error for very short series."""
        with pytest.raises(MetricsError):
            compute_acf_lag(short_series, max_lag=5)

class TestDFA:
    def test_hurst_white_noise(self, white_noise_series):
        """Hurst exponent for white noise should be around 0.5."""
        h = compute_dfa_hurst(white_noise_series)
        # Tolerance is generous due to finite sample effects
        assert 0.4 < h < 0.6, f"Hurst {h} not in expected range for white noise"

    def test_hurst_persistent(self, persistent_series):
        """Hurst exponent for persistent series should be > 0.5."""
        h = compute_dfa_hurst(persistent_series)
        assert h > 0.5, f"Hurst {h} should be > 0.5 for persistent series"

    def test_hurst_short_series_raises(self, short_series):
        """DFA should raise error for very short series."""
        with pytest.raises(MetricsError):
            compute_dfa_hurst(short_series)

class TestSpectralDensity:
    def test_spectral_peak_ratio_periodic(self, periodic_series):
        """Periodic series should have high spectral peak ratio."""
        ratio = compute_spectral_peak_ratio(periodic_series)
        assert ratio > 2.0, f"Peak ratio {ratio} too low for periodic series"

    def test_spectral_peak_ratio_white_noise(self, white_noise_series):
        """White noise should have low spectral peak ratio (near 1)."""
        ratio = compute_spectral_peak_ratio(white_noise_series)
        # White noise spectrum is flat, so ratio should be close to 1
        assert 0.5 < ratio < 3.0, f"Peak ratio {ratio} unexpected for white noise"

    def test_spectral_peak_ratio_short_series_raises(self, short_series):
        """Spectral analysis should raise error for very short series."""
        with pytest.raises(MetricsError):
            compute_spectral_peak_ratio(short_series)

class TestAllMetrics:
    def test_compute_all_metrics(self, white_noise_series):
        """Test that compute_all_metrics returns expected keys."""
        result = compute_all_metrics(white_noise_series)
        assert 'acf' in result
        assert 'hurst' in result
        assert 'spectral_peak_ratio' in result
        assert result['acf_lag_1'] is not None
        assert result['hurst'] is not None
        assert result['spectral_peak_ratio'] is not None

    def test_compute_all_metrics_partial_failure(self, short_series):
        """Test behavior when some metrics fail."""
        # This might fail entirely or return None for some fields depending on implementation
        # For now, we expect it to raise or return partial results
        # Based on current implementation, it raises for short series
        with pytest.raises(MetricsError):
            compute_all_metrics(short_series)

class TestMetricsForAllRealSeries:
    """Placeholder for integration-style tests with real data."""
    def test_compute_metrics_for_dataset(self, test_data_dir):
        """Test compute_metrics_for_dataset with a mock DataFrame."""
        data = {
            'datetime': pd.date_range('2020-01-01', periods=100, freq='D'),
            'value': np.random.normal(0, 1, 100)
        }
        df = pd.DataFrame(data)
        
        result = compute_metrics_for_dataset(df, value_column='value', date_column='datetime')
        
        assert 'n_points' in result
        assert result['n_points'] == 100
        assert 'metrics' in result
        assert result['metrics']['hurst'] is not None