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

# Set seed for reproducibility
set_seed(42)

@pytest.fixture
def white_noise_series():
    """Generate white noise series (H ≈ 0.5)."""
    np.random.seed(42)
    n = 1000
    return pd.Series(np.random.normal(0, 1, n), index=pd.date_range('2020-01-01', periods=n, freq='D'))

@pytest.fixture
def persistent_series():
    """Generate persistent series (H > 0.5) using fractional Gaussian noise approximation."""
    np.random.seed(42)
    n = 1000
    # Simple persistent series: cumulative sum of white noise
    white = np.random.normal(0, 1, n)
    persistent = np.cumsum(white)
    return pd.Series(persistent, index=pd.date_range('2020-01-01', periods=n, freq='D'))

@pytest.fixture
def periodic_series():
    """Generate series with strong periodic component."""
    np.random.seed(42)
    n = 1000
    t = np.arange(n)
    periodic = np.sin(2 * np.pi * t / 50) + np.random.normal(0, 0.1, n)
    return pd.Series(periodic, index=pd.date_range('2020-01-01', periods=n, freq='D'))

@pytest.fixture
def short_series():
    """Generate series too short for reliable metrics."""
    np.random.seed(42)
    n = 20
    return pd.Series(np.random.normal(0, 1, n), index=pd.date_range('2020-01-01', periods=n, freq='D'))

@pytest.fixture
def test_data_dir():
    """Create temporary directory with test CSV files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create test CSV files
        data = {
            'test_series1': np.random.normal(0, 1, 100),
            'test_series2': np.cumsum(np.random.normal(0, 1, 100))
        }
        for name, values in data.items():
            df = pd.DataFrame({'value': values}, 
                             index=pd.date_range('2020-01-01', periods=len(values), freq='D'))
            df.to_csv(tmpdir / f'{name}.csv')
        yield tmpdir

class TestACF:
    """Tests for ACF computation."""

    def test_white_noise_acf(self, white_noise_series):
        """White noise should have low ACF at lag 1."""
        result = compute_acf_lag20(white_noise_series)
        assert result['status'] == 'success'
        assert result['max_acf_lag1'] is not None
        # For white noise, ACF at lag 1 should be close to 0
        assert abs(result['max_acf_lag1']) < 0.3
        assert len(result['acf']) == 21  # lag 0 to 20

    def test_persistent_acf(self, persistent_series):
        """Persistent series should have higher ACF at lag 1."""
        result = compute_acf_lag20(persistent_series)
        assert result['status'] == 'success'
        assert result['max_acf_lag1'] is not None
        # Persistent series should have positive ACF
        assert result['max_acf_lag1'] > 0.3

    def test_short_series_acf(self, short_series):
        """Short series should return insufficient_length status."""
        result = compute_acf_lag20(short_series)
        assert result['status'] == 'insufficient_length'

    def test_acf_lag0_is_one(self, white_noise_series):
        """ACF at lag 0 should be 1."""
        result = compute_acf_lag20(white_noise_series)
        assert result['status'] == 'success'
        assert abs(result['acf'][0] - 1.0) < 0.01

class TestDFA:
    """Tests for DFA Hurst exponent computation."""

    def test_white_noise_hurst(self, white_noise_series):
        """White noise should have Hurst exponent near 0.5."""
        result = compute_dfa_hurst(white_noise_series)
        assert result['status'] == 'success'
        assert result['hurst_exponent'] is not None
        # For white noise, H should be close to 0.5
        assert 0.4 < result['hurst_exponent'] < 0.6

    def test_persistent_hurst(self, persistent_series):
        """Persistent series should have Hurst exponent > 0.5."""
        result = compute_dfa_hurst(persistent_series)
        assert result['status'] == 'success'
        assert result['hurst_exponent'] is not None
        # Persistent series should have H > 0.5
        assert result['hurst_exponent'] > 0.5

    def test_short_series_dfa(self, short_series):
        """Short series should return insufficient_length status."""
        result = compute_dfa_hurst(short_series)
        assert result['status'] == 'insufficient_length'

    def test_hurst_in_range(self, white_noise_series):
        """Hurst exponent should be in [0, 1]."""
        result = compute_dfa_hurst(white_noise_series)
        assert result['status'] == 'success'
        assert 0 <= result['hurst_exponent'] <= 1

class TestSpectralDensity:
    """Tests for spectral density peak ratio computation."""

    def test_white_noise_spectral(self, white_noise_series):
        """White noise should have low peak ratio (flat spectrum)."""
        result = compute_spectral_density_peak_ratio(white_noise_series)
        assert result['status'] == 'success'
        assert result['peak_ratio'] is not None
        # White noise should have peak ratio close to 1
        assert result['peak_ratio'] < 5

    def test_periodic_spectral(self, periodic_series):
        """Periodic series should have high peak ratio."""
        result = compute_spectral_density_peak_ratio(periodic_series)
        assert result['status'] == 'success'
        assert result['peak_ratio'] is not None
        # Periodic series should have high peak ratio
        assert result['peak_ratio'] > 2

    def test_short_series_spectral(self, short_series):
        """Short series should return insufficient_length status."""
        result = compute_spectral_density_peak_ratio(short_series)
        assert result['status'] == 'insufficient_length'

class TestAllMetrics:
    """Tests for combined metrics computation."""

    def test_compute_all_metrics_success(self, white_noise_series):
        """Should compute all metrics successfully."""
        result = compute_all_metrics(white_noise_series, 'test')
        assert result['status'] == 'success'
        assert result['series_name'] == 'test'
        assert result['acf']['status'] == 'success'
        assert result['hurst']['status'] == 'success'
        assert result['spectral']['status'] == 'success'

    def test_compute_all_metrics_short(self, short_series):
        """Short series should return too_short status."""
        result = compute_all_metrics(short_series, 'test')
        assert result['status'] == 'too_short'

    def test_compute_all_metrics_with_nan(self):
        """Should handle series with NaN values."""
        np.random.seed(42)
        n = 200
        data = np.random.normal(0, 1, n)
        data[50:60] = np.nan  # Insert NaNs
        series = pd.Series(data, index=pd.date_range('2020-01-01', periods=n, freq='D'))
        
        result = compute_all_metrics(series, 'test_nan')
        assert result['status'] in ['success', 'partial']
        assert result['clean_length'] < result['length']

class TestMetricsForAllRealSeries:
    """Tests for computing metrics across multiple series."""

    def test_compute_metrics_for_all_real_series(self, test_data_dir):
        """Should compute metrics for all CSV files in directory."""
        results = compute_metrics_for_all_real_series(processed_dir=test_data_dir)
        assert len(results) >= 1
        for r in results:
            assert 'series_name' in r
            assert 'status' in r

    def test_compute_metrics_with_output(self, test_data_dir):
        """Should save results to output path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / 'metrics_output'
            results = compute_metrics_for_all_real_series(
                processed_dir=test_data_dir,
                output_path=output_path
            )
            
            # Check that output files were created
            json_path = output_path.with_suffix('.json')
            csv_path = output_path.with_suffix('.csv')
            assert json_path.exists()
            assert csv_path.exists()