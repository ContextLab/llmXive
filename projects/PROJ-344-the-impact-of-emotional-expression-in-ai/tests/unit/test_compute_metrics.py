"""
Unit tests for cross-correlation logic in compute_metrics.

Tests the intra-modal consistency metric calculation using mocked time-series data.
The mock data is stored in tests/fixtures/mock_timeseries.npy.
"""
import os
import sys
import unittest
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.logging_config import get_logger
from code.utils import handle_corrupted_file

logger = get_logger(__name__)

# Ensure fixtures directory exists and contains mock data
FIXTURES_DIR = project_root / "tests" / "fixtures"
MOCK_TIMESERIES_PATH = FIXTURES_DIR / "mock_timeseries.npy"

class TestCrossCorrelationLogic(unittest.TestCase):
    """Unit tests for cross-correlation based consistency metrics."""

    @classmethod
    def setUpClass(cls):
        """Setup mock data for testing."""
        if not FIXTURES_DIR.exists():
            FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

        # Create deterministic mock time-series data
        # Shape: (N_samples, N_features)
        # Simulating facial AU (Action Units) and vocal prosody features
        np.random.seed(42)  # For reproducibility
        n_samples = 1000
        n_features = 5  # e.g., 5 facial AUs or 5 vocal features

        # Generate mock data with known correlation structure
        base_signal = np.random.randn(n_samples)
        # Add a delayed version of the base signal to create known correlation
        delayed_signal = np.roll(base_signal, 10)  # 10 sample lag
        
        # Create feature matrix where features have varying degrees of correlation
        mock_data = np.column_stack([
            base_signal + np.random.randn(n_samples) * 0.1,
            delayed_signal + np.random.randn(n_samples) * 0.1,
            base_signal * 0.8 + np.random.randn(n_samples) * 0.2,
            delayed_signal * 0.7 + np.random.randn(n_samples) * 0.2,
            np.random.randn(n_samples)  # Uncorrelated noise
        ])
        
        # Save to fixture
        np.save(str(MOCK_TIMESERIES_PATH), mock_data)
        logger.info(f"Created mock timeseries fixture at {MOCK_TIMESERIES_PATH}")

    def test_load_mock_timeseries(self):
        """Test that mock timeseries can be loaded successfully."""
        self.assertTrue(MOCK_TIMESERIES_PATH.exists(), "Mock timeseries file does not exist")
        data = np.load(str(MOCK_TIMESERIES_PATH))
        self.assertEqual(data.shape, (1000, 5), "Mock timeseries shape is incorrect")
        self.assertEqual(data.dtype, np.float64, "Mock timeseries dtype is incorrect")

    def test_compute_max_abs_cross_correlation(self):
        """Test the core cross-correlation logic with known data."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        data = np.load(str(MOCK_TIMESERIES_PATH))
        
        # Test with a lag range that should capture the known correlation
        # We know feature 0 and 1 have a 10-sample lag relationship
        max_lag = 20  # samples
        result = compute_max_abs_cross_correlation(data, max_lag=max_lag)
        
        self.assertIsInstance(result, float, "Result should be a float")
        self.assertTrue(0 <= result <= 1, "Correlation should be normalized between 0 and 1")
        self.assertGreater(result, 0.5, "Expected high correlation due to known structure in mock data")

    def test_compute_max_abs_cross_correlation_empty_input(self):
        """Test handling of empty input."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        empty_data = np.array([]).reshape(0, 5)
        result = compute_max_abs_cross_correlation(empty_data, max_lag=10)
        
        self.assertTrue(np.isnan(result), "Empty input should return NaN")

    def test_compute_max_abs_cross_correlation_single_feature(self):
        """Test with single feature (no cross-correlation possible)."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        single_feature = np.random.randn(100, 1)
        result = compute_max_abs_cross_correlation(single_feature, max_lag=10)
        
        # With only one feature, cross-correlation is not meaningful
        # Should return NaN or 0 depending on implementation
        self.assertTrue(np.isnan(result) or result == 0, 
                      "Single feature should return NaN or 0")

    def test_compute_max_abs_cross_correlation_lag_range(self):
        """Test that different lag ranges produce expected results."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        data = np.load(str(MOCK_TIMESERIES_PATH))
        
        # Small lag range might miss the correlation
        result_small_lag = compute_max_abs_cross_correlation(data, max_lag=5)
        # Larger lag range should capture the correlation
        result_large_lag = compute_max_abs_cross_correlation(data, max_lag=20)
        
        self.assertGreaterEqual(result_large_lag, result_small_lag,
                              "Larger lag range should capture more correlation")

    def test_compute_max_abs_cross_correlation_noise_only(self):
        """Test with purely random noise (should be low correlation)."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        noise_data = np.random.randn(1000, 5)
        result = compute_max_abs_cross_correlation(noise_data, max_lag=20)
        
        # Pure noise should have low correlation
        self.assertLess(result, 0.3, "Pure noise should have low cross-correlation")

    def test_compute_max_abs_cross_correlation_invalid_input(self):
        """Test handling of invalid input types."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        # Test with non-numpy input
        with self.assertRaises((TypeError, ValueError)):
            compute_max_abs_cross_correlation("invalid", max_lag=10)

    def test_compute_max_abs_cross_correlation_negative_lag(self):
        """Test handling of negative lag values."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        data = np.load(str(MOCK_TIMESERIES_PATH))
        
        # Negative lag should be treated as absolute value or raise error
        # Depending on implementation, we expect it to work with abs(lag)
        result = compute_max_abs_cross_correlation(data, max_lag=-10)
        
        self.assertIsInstance(result, float, "Negative lag should be handled")

    def test_compute_max_abs_cross_correlation_large_lag(self):
        """Test with very large lag values."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        data = np.load(str(MOCK_TIMESERIES_PATH))
        
        # Very large lag might exceed signal length
        result = compute_max_abs_cross_correlation(data, max_lag=2000)
        
        self.assertIsInstance(result, float, "Large lag should be handled")

    def test_compute_max_abs_cross_correlation_with_nan(self):
        """Test handling of data with NaN values."""
        from code.compute_metrics import compute_max_abs_cross_correlation
        
        data = np.load(str(MOCK_TIMESERIES_PATH)).copy()
        data[50, 2] = np.nan  # Insert NaN
        
        # Should handle NaN gracefully (either ignore or return NaN)
        result = compute_max_abs_cross_correlation(data, max_lag=10)
        
        # Implementation dependent: either NaN or computed on valid data
        self.assertTrue(np.isnan(result) or isinstance(result, float),
                      "NaN handling should result in float or NaN")

if __name__ == '__main__':
    unittest.main()
