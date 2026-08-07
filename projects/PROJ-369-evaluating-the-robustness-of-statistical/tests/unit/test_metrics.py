import pytest
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path

# Add src to path for imports if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from src.data.metrics import (
    MetricsError,
    compute_acf_lag,
    compute_dfa_hurst,
    compute_spectral_peak_ratio,
    compute_all_metrics,
    compute_metrics_for_dataset
)


class TestACFLag:
    def test_acf_white_noise(self):
        """Test ACF on white noise (should be near zero for lags > 0)."""
        np.random.seed(42)
        noise = np.random.normal(0, 1, 1000)
        acf = compute_acf_lag(noise, max_lag=5)
        
        for lag, val in acf.items():
            # Allow some tolerance for randomness
            assert abs(val) < 0.1, f"ACF at lag {lag} is {val}, expected near 0 for white noise"

    def test_acf_constant(self):
        """Test ACF on constant series (should be 0 or undefined, handled as 0)."""
        constant = np.ones(100)
        acf = compute_acf_lag(constant, max_lag=5)
        for val in acf.values():
            assert val == 0.0

    def test_acf_perfect_correlation(self):
        """Test ACF on a perfectly correlated series (lag 1 should be ~1)."""
        # Create a series where x[t] = x[t-1] + noise (random walk-ish but stable enough for short lag)
        # Better: x[t] = 0.9 * x[t-1] + noise
        np.random.seed(42)
        n = 1000
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = 0.9 * x[i-1] + np.random.normal(0, 0.1)
        
        acf = compute_acf_lag(x, max_lag=5)
        # Lag 1 should be high
        assert acf[1] > 0.8, f"Expected high ACF at lag 1, got {acf[1]}"


class TestDFAHurst:
    def test_hurst_white_noise(self):
        """Test Hurst exponent on white noise (should be ~0.5)."""
        np.random.seed(42)
        noise = np.random.normal(0, 1, 2000) # Need larger N for stable DFA
        hurst = compute_dfa_hurst(noise)
        
        # White noise H should be close to 0.5
        assert 0.4 <= hurst <= 0.6, f"Hurst for white noise should be ~0.5, got {hurst}"

    def test_hurst_persistent(self):
        """Test Hurst on persistent series (H > 0.5)."""
        # Generate a series with long memory (approximate)
        np.random.seed(42)
        n = 2000
        x = np.cumsum(np.random.normal(0, 1, n)) # Random walk, H=1.5 theoretically for non-stationary, 
        # But DFA on random walk often yields H ~ 1.0 or slightly less depending on detrending.
        # Let's use a fractional noise generator if available, or just a strong trend.
        # For testing, a simple trend:
        x = np.linspace(0, 10, n) + np.random.normal(0, 0.1, n)
        
        hurst = compute_dfa_hurst(x)
        # Trended series usually yields H > 0.5
        assert hurst > 0.5, f"Persistent series should have H > 0.5, got {hurst}"

    def test_hurst_too_short(self):
        """Test Hurst on series too short for DFA."""
        short_series = np.random.normal(0, 1, 5)
        with pytest.raises(MetricsError):
            compute_dfa_hurst(short_series, min_scale=4)


class TestSpectralPeakRatio:
    def test_spectral_sine(self):
        """Test spectral ratio on a pure sine wave (should have high peak)."""
        t = np.linspace(0, 10, 1000)
        freq = 5
        sine_wave = np.sin(2 * np.pi * freq * t)
        
        ratio = compute_spectral_peak_ratio(sine_wave)
        # Sine wave has a very sharp peak, ratio should be high
        assert ratio > 10, f"Sine wave should have high spectral ratio, got {ratio}"

    def test_spectral_noise(self):
        """Test spectral ratio on white noise (should be low)."""
        np.random.seed(42)
        noise = np.random.normal(0, 1, 1000)
        ratio = compute_spectral_peak_ratio(noise)
        # Noise should have ratio close to 1 (flat spectrum)
        assert ratio < 5, f"Noise should have low spectral ratio, got {ratio}"

    def test_spectral_empty(self):
        """Test with empty input."""
        with pytest.raises(MetricsError):
            compute_spectral_peak_ratio(np.array([]))


class TestComputeAllMetrics:
    def test_full_metrics(self):
        """Test computing all metrics on a generated series."""
        np.random.seed(42)
        series = np.random.normal(0, 1, 1000)
        
        results = compute_all_metrics(series)
        
        assert 'acf_lag' in results
        assert 'hurst' in results
        assert 'spectral_peak_ratio' in results
        
        assert isinstance(results['acf_lag'], dict)
        assert isinstance(results['hurst'], float)
        assert isinstance(results['spectral_peak_ratio'], float)

class TestComputeMetricsForDataset:
    def test_compute_from_csv(self, tmp_path):
        """Test computing metrics from a CSV file."""
        # Create a test CSV
        data = {
            'date': pd.date_range(start='2020-01-01', periods=100),
            'value': np.random.normal(0, 1, 100)
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "test_data.csv"
        df.to_csv(csv_path, index=False)
        
        results = compute_metrics_for_dataset(str(csv_path), value_column='value')
        
        assert results['n_points'] == 100
        assert 'hurst' in results
        assert 'acf_lag' in results
        
    def test_missing_column(self, tmp_path):
        """Test error when column is missing."""
        data = {'date': [1, 2, 3], 'other': [4, 5, 6]}
        df = pd.DataFrame(data)
        csv_path = tmp_path / "test_missing.csv"
        df.to_csv(csv_path, index=False)
        
        with pytest.raises(MetricsError):
            compute_metrics_for_dataset(str(csv_path), value_column='missing_col')