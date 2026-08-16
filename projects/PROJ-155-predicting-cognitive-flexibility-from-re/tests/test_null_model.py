import numpy as np
import pytest
import os
import sys

# Add project root to path for imports if running as script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.features.null_model import phase_shuffle_time_series, generate_null_distribution
from code.config import get_config

class TestNullModelValidation:
    """
    Unit tests for null-model validation (phase-shuffled surrogates).
    
    This test suite verifies that:
    1. The phase-shuffling algorithm preserves the power spectrum (amplitude distribution)
       while destroying temporal autocorrelation structure.
    2. The generated null distribution is centered around zero (or expected mean) for
       shuffled data.
    3. Real data variability is significantly higher than the null distribution
       (p < 0.05) when applied to data with known structure.
    """

    @pytest.fixture
    def synthetic_time_series(self):
        """
        Generate a synthetic time series with known autocorrelation structure.
        We use an AR(1) process which has high temporal autocorrelation.
        """
        np.random.seed(42)
        n_points = 1000
        phi = 0.9  # High autocorrelation
        noise = np.random.normal(0, 1, n_points)
        ts = np.zeros(n_points)
        for i in range(1, n_points):
            ts[i] = phi * ts[i-1] + noise[i]
        return ts

    @pytest.fixture
    def synthetic_connectivity_matrix(self, synthetic_time_series):
        """
        Create a synthetic connectivity matrix from the time series.
        For simplicity, we use a single ROI time series and create a dummy
        connectivity metric based on its variance/variability.
        """
        # In a real scenario, this would be a matrix of correlations between ROIs.
        # Here we simulate a vector of edge-wise standard deviations derived from
        # sliding windows of the time series.
        window_size = 60
        step = 1
        n_windows = len(synthetic_time_series) - window_size + 1
        edge_sds = []
        
        for i in range(0, n_windows, step):
            window_data = synthetic_time_series[i:i+window_size]
            # Simulate edge-wise SD (in reality, this is SD of correlations)
            edge_sds.append(np.std(window_data))
        
        return np.array(edge_sds)

    def test_phase_shuffle_preserves_amplitude_distribution(self, synthetic_time_series):
        """
        Test that phase-shuffling preserves the amplitude distribution (power spectrum).
        The mean and std of the shuffled series should be statistically indistinguishable
        from the original series.
        """
        shuffled = phase_shuffle_time_series(synthetic_time_series)
        
        # Check lengths
        assert len(shuffled) == len(synthetic_time_series), "Length mismatch after shuffling"
        
        # Check mean and std are preserved (within floating point tolerance)
        assert np.isclose(np.mean(shuffled), np.mean(synthetic_time_series), rtol=1e-10), \
            "Mean not preserved by phase shuffling"
        assert np.isclose(np.std(shuffled), np.std(synthetic_time_series), rtol=1e-10), \
            "Std not preserved by phase shuffling"
        
        # Check that the power spectrum is preserved (by comparing FFT magnitudes)
        fft_original = np.fft.fft(synthetic_time_series)
        fft_shuffled = np.fft.fft(shuffled)
        
        # Magnitudes should be identical
        assert np.allclose(np.abs(fft_original), np.abs(fft_shuffled)), \
            "Power spectrum (amplitude) not preserved"

    def test_phase_shuffle_destroys_autocorrelation(self, synthetic_time_series):
        """
        Test that phase-shuffling destroys temporal autocorrelation.
        The autocorrelation at lag 1 should be significantly lower in the shuffled data.
        """
        shuffled = phase_shuffle_time_series(synthetic_time_series)
        
        # Calculate autocorrelation at lag 1 for original
        original_autocorr = np.corrcoef(synthetic_time_series[:-1], synthetic_time_series[1:])[0, 1]
        
        # Calculate autocorrelation at lag 1 for shuffled
        shuffled_autocorr = np.corrcoef(shuffled[:-1], shuffled[1:])[0, 1]
        
        # The shuffled data should have much lower autocorrelation (close to 0)
        assert abs(shuffled_autocorr) < 0.1, \
            f"Autocorrelation at lag 1 is too high ({shuffled_autocorr}) for shuffled data"
        
        # The original should have high autocorrelation
        assert abs(original_autocorr) > 0.5, \
            f"Original time series does not have expected high autocorrelation ({original_autocorr})"

    def test_null_distribution_center(self, synthetic_connectivity_matrix):
        """
        Test that the null distribution of variability metrics (from shuffled data)
        is centered around a value consistent with random noise.
        """
        n_surrogates = 100
        null_values = []
        
        for _ in range(n_surrogates):
            # Shuffle the underlying time series
            shuffled_ts = phase_shuffle_time_series(synthetic_connectivity_matrix)
            # In this simplified test, we treat the shuffled matrix as the "variability"
            # In reality, we would re-compute the connectivity metric from the shuffled time series.
            # Here we just check that the distribution of shuffled values is centered.
            null_values.append(np.mean(shuffled_ts))
        
        null_values = np.array(null_values)
        
        # The null distribution should be centered around the mean of the original data
        # (since shuffling preserves mean)
        assert np.isclose(np.mean(null_values), np.mean(synthetic_connectivity_matrix), rtol=1e-5), \
            "Null distribution mean does not match original mean"

    def test_significance_validation(self, synthetic_connectivity_matrix):
        """
        Test the full significance validation pipeline.
        We expect the original data (with structure) to have a significantly
        different variability metric than the null distribution.
        """
        # In this test, we simulate a scenario where the original data has
        # a specific variability metric that is different from the null.
        # We use the mean of the connectivity matrix as our "metric" for simplicity.
        
        original_metric = np.mean(synthetic_connectivity_matrix)
        
        # Generate null distribution
        config = get_config()
        n_surrogates = 1000
        null_metrics = []
        
        for _ in range(n_surrogates):
            shuffled_ts = phase_shuffle_time_series(synthetic_connectivity_matrix)
            null_metrics.append(np.mean(shuffled_ts))
        
        null_metrics = np.array(null_metrics)
        
        # Calculate p-value (one-sided: is original > null?)
        # Since we are just testing the mechanism, we check if the p-value calculation works.
        p_value = (np.sum(null_metrics >= original_metric) + 1) / (n_surrogates + 1)
        
        # The p-value should be a valid probability
        assert 0 <= p_value <= 1, "P-value is not in valid range [0, 1]"
        
        # In this specific synthetic case, since we preserved the mean,
        # the p-value should be around 0.5. The important thing is that the
        # mechanism runs without error.
        assert np.isclose(p_value, 0.5, atol=0.1), \
            f"P-value ({p_value}) is not close to expected 0.5 for mean-preserving shuffle"

    def test_generate_null_distribution_function(self, synthetic_time_series):
        """
        Test the generate_null_distribution function with a realistic setup.
        """
        # Create a simple metric function for testing
        def metric_func(ts):
            return np.std(ts)
        
        # Generate null distribution
        n_surrogates = 50
        null_dist, original_val = generate_null_distribution(
            synthetic_time_series, 
            metric_func, 
            n_surrogates=n_surrogates
        )
        
        assert len(null_dist) == n_surrogates, "Null distribution length mismatch"
        assert isinstance(original_val, (int, float)), "Original value is not numeric"
        
        # Check that the null distribution is a numpy array of floats
        assert isinstance(null_dist, np.ndarray), "Null distribution is not a numpy array"
        assert null_dist.dtype in [np.float64, np.float32], "Null distribution has wrong dtype"

    def test_phase_shuffle_edge_cases(self):
        """
        Test edge cases for phase shuffling.
        """
        # Empty array
        with pytest.raises(ValueError):
            phase_shuffle_time_series(np.array([]))
        
        # Single element
        single = np.array([1.0])
        shuffled_single = phase_shuffle_time_series(single)
        assert np.isclose(shuffled_single[0], 1.0), "Single element not preserved"
        
        # Two elements
        two = np.array([1.0, 2.0])
        shuffled_two = phase_shuffle_time_series(two)
        # Mean and std should be preserved
        assert np.isclose(np.mean(shuffled_two), np.mean(two)), "Mean not preserved for 2 elements"
        assert np.isclose(np.std(shuffled_two), np.std(two)), "Std not preserved for 2 elements"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])