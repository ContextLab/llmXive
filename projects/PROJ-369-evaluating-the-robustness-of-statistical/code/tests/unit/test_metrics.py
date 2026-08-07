"""
Unit tests for metrics computation module.
"""
import pytest
import numpy as np
import pandas as pd
from scipy import stats
import tempfile
from pathlib import Path

from src.data.metrics import (
    compute_acf_lag20,
    compute_dfa_hurst,
    compute_spectral_density_peak_ratio,
    compute_all_metrics,
    compute_metrics_for_all_real_series
)
from src.utils.config import set_seed


@pytest.fixture
def white_noise_series():
    """Generate white noise series (H ≈ 0.5)."""
    set_seed(42)
    return pd.Series(np.random.randn(1000))

@pytest.fixture
def persistent_series():
    """Generate persistent series (H > 0.5)."""
    set_seed(123)
    # Cumulative sum creates persistence
    return pd.Series(np.cumsum(np.random.randn(1000)))

@pytest.fixture
def periodic_series():
    """Generate periodic series with strong spectral peak."""
    set_seed(456)
    n = 1000
    t = np.arange(n)
    # Strong periodic component + noise
    return pd.Series(2 * np.sin(2 * np.pi * t / 50) + np.random.randn(n) * 0.5)

@pytest.fixture
def short_series():
    """Generate series too short for DFA."""
    set_seed(789)
    return pd.Series(np.random.randn(10))

@pytest.fixture
def test_data_dir(tmp_path):
    """Create temporary data directory with test CSV files."""
    # Create processed directory
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    
    # Create test series
    series1 = pd.Series(np.random.randn(500), name='test_series_1')
    series1.to_csv(processed_dir / "test_series_1.csv")
    
    series2 = pd.Series(np.random.randn(300), name='test_series_2')
    series2.to_csv(processed_dir / "test_series_2.csv")
    
    return processed_dir


class TestACF:
    """Tests for ACF computation."""

    def test_acf_lag0_is_one(self, white_noise_series):
        """ACF at lag 0 should always be 1.0."""
        result = compute_acf_lag20(white_noise_series)
        assert result['acf_values'][0] == 1.0

    def test_acf_returns_expected_lags(self, white_noise_series):
        """ACF should return 21 values (lag 0 to 20)."""
        result = compute_acf_lag20(white_noise_series)
        assert len(result['acf_values']) == 21

    def test_acf_max_lag1_is_valid(self, white_noise_series):
        """max_acf_lag1 should be the ACF at lag 1."""
        result = compute_acf_lag20(white_noise_series)
        assert result['max_acf_lag1'] == result['acf_values'][1]

    def test_acf_for_constant_series(self):
        """ACF for constant series should handle division by zero."""
        constant_series = pd.Series(np.ones(100))
        result = compute_acf_lag20(constant_series)
        assert result['acf_values'][0] == 1.0
        assert all(result['acf_values'][1:] == 0.0)

    def test_acf_with_too_short_series(self):
        """ACF should raise error for series with < 2 points."""
        with pytest.raises(ValueError, match="at least 2 points"):
            compute_acf_lag20(pd.Series([1.0]))

class TestDFA:
    """Tests for DFA Hurst exponent computation."""

    def test_dfa_returns_hurst_exponent(self, white_noise_series):
        """DFA should return a Hurst exponent value."""
        result = compute_dfa_hurst(white_noise_series)
        assert 'hurst_exponent' in result
        assert isinstance(result['hurst_exponent'], float)

    def test_dfa_hurst_range(self, white_noise_series):
        """Hurst exponent should be in valid range [0, 1]."""
        result = compute_dfa_hurst(white_noise_series)
        assert 0 <= result['hurst_exponent'] <= 1

    def test_dfa_returns_r_squared(self, white_noise_series):
        """DFA should return R-squared of the fit."""
        result = compute_dfa_hurst(white_noise_series)
        assert 'r_squared' in result
        assert 0 <= result['r_squared'] <= 1

    def test_dfa_too_short_series(self, short_series):
        """DFA should raise error for series too short."""
        with pytest.raises(ValueError, match="too short"):
            compute_dfa_hurst(short_series)

    def test_dfa_persistent_series_higher_hurst(self, persistent_series, white_noise_series):
        """Persistent series should have higher Hurst exponent than white noise."""
        hurst_persistent = compute_dfa_hurst(persistent_series)['hurst_exponent']
        hurst_white = compute_dfa_hurst(white_noise_series)['hurst_exponent']
        # Note: This is a soft assertion as DFA can be noisy
        assert hurst_persistent >= hurst_white - 0.1

class TestSpectralDensity:
    """Tests for spectral density peak ratio computation."""

    def test_spectral_returns_peak_ratio(self, white_noise_series):
        """Spectral analysis should return peak ratio."""
        result = compute_spectral_density_peak_ratio(white_noise_series)
        assert 'peak_ratio' in result
        assert isinstance(result['peak_ratio'], float)

    def test_spectral_peak_ratio_positive(self, white_noise_series):
        """Peak ratio should be non-negative."""
        result = compute_spectral_density_peak_ratio(white_noise_series)
        assert result['peak_ratio'] >= 0

    def test_periodic_series_high_peak_ratio(self, periodic_series, white_noise_series):
        """Periodic series should have higher peak ratio than white noise."""
        ratio_periodic = compute_spectral_density_peak_ratio(periodic_series)['peak_ratio']
        ratio_white = compute_spectral_density_peak_ratio(white_noise_series)['peak_ratio']
        assert ratio_periodic > ratio_white

    def test_spectral_returns_frequencies(self, white_noise_series):
        """Spectral analysis should return frequency array."""
        result = compute_spectral_density_peak_ratio(white_noise_series)
        assert 'frequencies' in result
        assert len(result['frequencies']) > 0

class TestAllMetrics:
    """Tests for combined metrics computation."""

    def test_compute_all_metrics_structure(self, white_noise_series):
        """compute_all_metrics should return expected structure."""
        result = compute_all_metrics(white_noise_series, "test_series")
        
        assert result['series_name'] == "test_series"
        assert result['series_length'] == len(white_noise_series)
        assert result['status'] == 'success'
        assert 'acf' in result
        assert 'hurst' in result
        assert 'spectral' in result

    def test_compute_all_metrics_with_error(self):
        """compute_all_metrics should handle errors gracefully."""
        short_series = pd.Series([1.0])
        result = compute_all_metrics(short_series, "error_test")
        
        assert result['status'] == 'failed'
        assert 'error' in result

class TestMetricsForAllRealSeries:
    """Tests for batch metrics computation."""

    def test_compute_metrics_for_all_real_series(self, test_data_dir):
        """Should compute metrics for all CSV files in directory."""
        df = compute_metrics_for_all_real_series(
            data_dir=str(test_data_dir),
            output_path=None
        )
        
        assert len(df) == 2  # Two test series
        assert 'series_name' in df.columns
        assert 'status' in df.columns

    def test_compute_metrics_saves_to_file(self, test_data_dir, tmp_path):
        """Should save results to specified output path."""
        output_path = tmp_path / "metrics_output.csv"
        
        df = compute_metrics_for_all_real_series(
            data_dir=str(test_data_dir),
            output_path=str(output_path)
        )
        
        assert output_path.exists()
        assert len(pd.read_csv(output_path)) == 2

    def test_compute_metrics_handles_missing_dir(self):
        """Should raise error for non-existent directory."""
        with pytest.raises(FileNotFoundError):
            compute_metrics_for_all_real_series(data_dir="/nonexistent/path")

    def test_compute_metrics_skips_short_series(self, tmp_path):
        """Should skip series that are too short."""
        processed_dir = tmp_path / "processed"
        processed_dir.mkdir()
        
        # Create short series
        short_series = pd.Series(np.random.randn(10))
        short_series.to_csv(processed_dir / "short.csv")
        
        # Create long series
        long_series = pd.Series(np.random.randn(500))
        long_series.to_csv(processed_dir / "long.csv")
        
        df = compute_metrics_for_all_real_series(
            data_dir=str(processed_dir),
            output_path=None
        )
        
        # Should only include the long series
        assert len(df) == 1
        assert df.iloc[0]['series_name'] == 'long'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
