import pytest
import numpy as np
import pandas as pd
from scipy import stats
import tempfile
from pathlib import Path
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.data.metrics import (
    compute_acf_lag,
    compute_dfa_hurst,
    compute_spectral_peak_ratio,
    compute_all_metrics,
    compute_metrics_for_dataset,
    MetricsError
)

@pytest.fixture
def white_noise_series():
    """Generate white noise series (H ~ 0.5)"""
    np.random.seed(42)
    return np.random.randn(1000)

@pytest.fixture
def persistent_series():
    """Generate persistent series (H > 0.5)"""
    np.random.seed(42)
    # Create a series with positive autocorrelation
    n = 1000
    series = np.zeros(n)
    for i in range(1, n):
        series[i] = 0.8 * series[i-1] + np.random.randn()
    return series

@pytest.fixture
def periodic_series():
    """Generate periodic series"""
    np.random.seed(42)
    t = np.linspace(0, 10 * np.pi, 1000)
    return np.sin(t) + 0.1 * np.random.randn(1000)

@pytest.fixture
def short_series():
    """Generate short series for edge case testing"""
    np.random.seed(42)
    return np.random.randn(20)

@pytest.fixture
def test_data_dir():
    """Temporary directory for test data"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

class TestACF:
    def test_acf_lag_zero_is_one(self, white_noise_series):
        """ACF at lag 0 should always be 1.0"""
        acf = compute_acf_lag(white_noise_series, max_lag=5)
        assert acf[0] == 1.0

    def test_acf_decay_for_white_noise(self, white_noise_series):
        """ACF should decay quickly for white noise"""
        acf = compute_acf_lag(white_noise_series, max_lag=20)
        # Most values should be close to 0
        assert np.allclose(acf[1:], 0, atol=0.1)

    def test_acf_persistence(self, persistent_series):
        """ACF should decay slowly for persistent series"""
        acf = compute_acf_lag(persistent_series, max_lag=20)
        # First few lags should be significantly positive
        assert acf[1] > 0.5
        assert acf[5] > 0.2

    def test_acf_too_short_series(self, short_series):
        """Should raise error for series too short for requested lags"""
        with pytest.raises(MetricsError):
            compute_acf_lag(short_series, max_lag=100)

    def test_acf_output_length(self, white_noise_series):
        """ACF output should have max_lag + 1 elements"""
        acf = compute_acf_lag(white_noise_series, max_lag=20)
        assert len(acf) == 21

class TestDFA:
    def test_hurst_white_noise(self, white_noise_series):
        """Hurst exponent for white noise should be ~0.5"""
        hurst = compute_dfa_hurst(white_noise_series)
        assert 0.4 < hurst < 0.6

    def test_hurst_persistent(self, persistent_series):
        """Hurst exponent for persistent series should be > 0.5"""
        hurst = compute_dfa_hurst(persistent_series)
        assert hurst > 0.5

    def test_hurst_too_short(self, short_series):
        """Should raise error for series too short for DFA"""
        with pytest.raises(MetricsError):
            compute_dfa_hurst(short_series)

class TestSpectralDensity:
    def test_spectral_ratio_computation(self, white_noise_series):
        """Spectral peak ratio should be computable for valid series"""
        ratio = compute_spectral_peak_ratio(white_noise_series)
        assert isinstance(ratio, float)
        assert np.isfinite(ratio)

    def test_spectral_ratio_periodic(self, periodic_series):
        """Periodic series should have high spectral peak ratio"""
        ratio = compute_spectral_peak_ratio(periodic_series)
        # Periodic series should have strong peaks
        assert ratio > 1.0

    def test_spectral_ratio_too_short(self, short_series):
        """Should raise error for series too short"""
        with pytest.raises(MetricsError):
            compute_spectral_peak_ratio(short_series)

    def test_spectral_ratio_numerical_stability(self):
        """Test handling of numerical instability"""
        # Series with very low variance
        series = np.ones(100) * 1e-10
        # Should not crash, but might return unexpected values
        ratio = compute_spectral_peak_ratio(series)
        assert np.isfinite(ratio)

class TestAllMetrics:
    def test_compute_all_metrics_structure(self, white_noise_series):
        """Test that compute_all_metrics returns correct structure"""
        metrics = compute_all_metrics(white_noise_series)
        
        assert 'acf_vector' in metrics
        assert 'hurst' in metrics
        assert 'spectral_peak_ratio' in metrics
        assert 'variance_fallback' in metrics
        
        assert len(metrics['acf_vector']) == 21
        assert isinstance(metrics['variance_fallback'], float)

    def test_variance_fallback_always_present(self, short_series):
        """Variance fallback should always be present even if other metrics fail"""
        # Use a series that might cause spectral analysis to fail
        series = np.ones(10)  # Very short, might fail spectral
        metrics = compute_all_metrics(series)
        
        assert 'variance_fallback' in metrics
        assert metrics['variance_fallback'] == 0.0  # Constant series has 0 variance

    def test_metrics_with_nan_handling(self):
        """Test handling of series with NaN values"""
        series = np.random.randn(100)
        series[50] = np.nan
        # Should handle gracefully or raise appropriate error
        try:
            metrics = compute_all_metrics(series)
            # If it doesn't raise, variance should still be computed
            assert 'variance_fallback' in metrics
        except (MetricsError, ValueError):
            # Expected behavior for NaN handling
            pass

class TestMetricsForAllRealSeries:
    def test_compute_metrics_for_dataset(self, white_noise_series):
        """Test compute_metrics_for_dataset with source identification"""
        result = compute_metrics_for_dataset(white_noise_series, source="test_source")
        
        assert result['source'] == "test_source"
        assert result['length'] == 1000
        assert 'hurst' in result
        assert 'acf_vector' in result
        assert 'spectral_peak_ratio' in result
        assert 'variance_fallback' in result

    def test_pandas_series_support(self, test_data_dir):
        """Test that pandas Series are handled correctly"""
        series = pd.Series(np.random.randn(100))
        result = compute_metrics_for_dataset(series, source="pandas_test")
        
        assert result['source'] == "pandas_test"
        assert result['length'] == 100
        assert 'variance_fallback' in result
        assert result['variance_fallback'] == pytest.approx(1.0, abs=0.2)

    def test_variance_fallback_in_output(self):
        """Verify variance_fallback is explicitly stored in output"""
        series = np.random.randn(1000)
        result = compute_metrics_for_dataset(series, source="variance_test")
        
        assert 'variance_fallback' in result
        expected_var = float(np.var(series))
        assert result['variance_fallback'] == pytest.approx(expected_var, rel=1e-5)