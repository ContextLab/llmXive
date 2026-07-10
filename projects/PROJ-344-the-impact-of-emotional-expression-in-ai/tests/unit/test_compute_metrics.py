"""
Unit tests for cross-correlation logic in compute_metrics module.

Tests the compute_max_abs_cross_correlation function using mocked time-series data.
"""
import unittest
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from compute_metrics import compute_max_abs_cross_correlation, validate_feature_input

class TestCrossCorrelation(unittest.TestCase):
    """Test cases for cross-correlation metrics."""
    
    def setUp(self):
        """Set up test fixtures including mock time-series data."""
        self.fixture_dir = Path(__file__).parent.parent / "fixtures"
        self.fixture_dir.mkdir(exist_ok=True)
        self.mock_file = self.fixture_dir / "mock_timeseries.npy"
        
        # Generate realistic mock time-series data if it doesn't exist
        # This simulates facial (valence) and vocal (pitch) features over time
        np.random.seed(42)  # Deterministic for reproducibility
        n_points = 1000
        t = np.linspace(0, 100, n_points)
        
        # Create correlated signals with a known lag
        base_signal = np.sin(t / 5.0) + np.random.normal(0, 0.1, n_points)
        # Vocal signal lags facial signal by 50 samples (approx 5 seconds at 10Hz)
        vocal_signal = np.roll(base_signal, 50) + np.random.normal(0, 0.1, n_points)
        
        # Save to file for the test to load
        np.save(self.mock_file, {
            'facial': base_signal,
            'vocal': vocal_signal,
            'time': t
        })
    
    def test_load_mock_data(self):
        """Verify that mock time-series data can be loaded."""
        self.assertTrue(self.mock_file.exists(), "Mock data file not found")
        data = np.load(self.mock_file, allow_pickle=True).item()
        self.assertIn('facial', data)
        self.assertIn('vocal', data)
        self.assertEqual(len(data['facial']), 1000)
        self.assertEqual(len(data['vocal']), 1000)
    
    def test_compute_max_abs_cross_correlation_known_lag(self):
        """Test cross-correlation with known lagged signals."""
        data = np.load(self.mock_file, allow_pickle=True).item()
        facial = data['facial']
        vocal = data['vocal']
        
        # Compute cross-correlation
        max_corr, optimal_lag = compute_max_abs_cross_correlation(facial, vocal)
        
        # Verify correlation is high (signals are correlated)
        self.assertGreater(max_corr, 0.8, "Correlation should be high for similar signals")
        
        # Verify optimal lag is near the injected lag (50 samples)
        # Allow some tolerance due to noise
        self.assertLess(abs(optimal_lag - 50), 10, "Optimal lag should be near 50 samples")
    
    def test_compute_max_abs_cross_correlation_uncorrelated(self):
        """Test cross-correlation with uncorrelated noise."""
        np.random.seed(123)
        signal_a = np.random.normal(0, 1, 500)
        signal_b = np.random.normal(0, 1, 500)
        
        max_corr, optimal_lag = compute_max_abs_cross_correlation(signal_a, signal_b)
        
        # Correlation should be low for uncorrelated noise
        self.assertLess(abs(max_corr), 0.3, "Correlation should be low for uncorrelated signals")
    
    def test_compute_max_abs_cross_correlation_negative_lag(self):
        """Test cross-correlation where signal B leads signal A."""
        np.random.seed(456)
        base = np.random.randn(500)
        # Signal B leads by 30 samples
        signal_a = np.roll(base, 30)
        signal_b = base
        
        max_corr, optimal_lag = compute_max_abs_cross_correlation(signal_a, signal_b)
        
        # Optimal lag should be negative (B leads A)
        self.assertLess(optimal_lag, 0, "Optimal lag should be negative when B leads A")
        self.assertGreater(abs(max_corr), 0.5, "Correlation should be significant")
    
    def test_validate_feature_input_shapes(self):
        """Test input validation for mismatched array lengths."""
        np.random.seed(789)
        short = np.random.randn(100)
        long = np.random.randn(200)
        
        # This should raise a ValueError
        with self.assertRaises(ValueError):
            validate_feature_input(short, long)
    
    def test_validate_feature_input_valid(self):
        """Test input validation for valid arrays."""
        np.random.seed(999)
        a = np.random.randn(100)
        b = np.random.randn(100)
        
        # Should not raise
        try:
            validate_feature_input(a, b)
        except Exception:
            self.fail("validate_feature_input raised unexpectedly for valid input")

if __name__ == '__main__':
    unittest.main()