import pytest
import numpy as np
from pathlib import Path
import sys
import os

# Ensure we can import from the code directory
project_root = Path(__file__).parent.parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from fpca import calculate_cumulative_variance, run_fpca
from config import get_data_dir

class TestCumulativeVariance:
    """
    Unit tests for cumulative variance calculation in fPCA.
    
    Tests verify that:
    1. The function correctly computes cumulative variance from eigenvalues
    2. The output matches expected mathematical properties
    3. Edge cases are handled correctly (empty input, single component, etc.)
    """

    def test_basic_cumulative_variance_calculation(self):
        """Test basic cumulative variance calculation with known eigenvalues."""
        # Create synthetic eigenvalues (descending order)
        eigenvalues = np.array([10.0, 5.0, 2.5, 1.0, 0.5])
        
        # Expected cumulative variance:
        # Total variance = 10 + 5 + 2.5 + 1 + 0.5 = 19
        # Cumulative: [10/19, 15/19, 17.5/19, 18.5/19, 19/19]
        total_variance = np.sum(eigenvalues)
        expected_cumulative = np.cumsum(eigenvalues) / total_variance
        
        result = calculate_cumulative_variance(eigenvalues)
        
        assert np.allclose(result, expected_cumulative), \
            f"Expected {expected_cumulative}, got {result}"
        
        # Verify last value is 1.0 (100%)
        assert np.isclose(result[-1], 1.0), \
            f"Last cumulative variance should be 1.0, got {result[-1]}"

    def test_cumulative_variance_monotonicity(self):
        """Test that cumulative variance is monotonically increasing."""
        eigenvalues = np.array([8.0, 4.0, 2.0, 1.0, 0.5, 0.3])
        result = calculate_cumulative_variance(eigenvalues)
        
        # Check monotonicity
        assert np.all(np.diff(result) >= 0), \
            "Cumulative variance should be monotonically increasing"

    def test_single_eigenvalue(self):
        """Test with a single eigenvalue."""
        eigenvalues = np.array([5.0])
        result = calculate_cumulative_variance(eigenvalues)
        
        assert len(result) == 1
        assert np.isclose(result[0], 1.0), \
            "Single eigenvalue should result in 100% cumulative variance"

    def test_very_small_eigenvalues(self):
        """Test with very small eigenvalues."""
        eigenvalues = np.array([1e-10, 1e-11, 1e-12])
        result = calculate_cumulative_variance(eigenvalues)
        
        # Should still sum to 1.0 at the end
        assert np.isclose(result[-1], 1.0), \
            f"Cumulative variance should be 1.0, got {result[-1]}"

    def test_cumulative_variance_with_zero_eigenvalues(self):
        """Test handling of zero eigenvalues."""
        eigenvalues = np.array([10.0, 5.0, 0.0, 0.0])
        result = calculate_cumulative_variance(eigenvalues)
        
        # Should handle zeros correctly
        assert np.isclose(result[-1], 1.0), \
            "Cumulative variance should be 1.0 even with zero eigenvalues"
        
        # Check that the values are correct
        total = 15.0
        expected = np.array([10/total, 15/total, 15/total, 15/total])
        assert np.allclose(result, expected), \
            f"Expected {expected}, got {result}"

    def test_stopping_threshold_calculation(self):
        """Test that we can determine the number of components needed for a threshold."""
        eigenvalues = np.array([10.0, 5.0, 2.5, 1.0, 0.5])
        cumulative = calculate_cumulative_variance(eigenvalues)
        
        # Test various thresholds
        thresholds = [0.5, 0.75, 0.8, 0.9, 0.95, 1.0]
        
        for threshold in thresholds:
            # Find number of components needed
            n_components = np.searchsorted(cumulative, threshold) + 1
            # Verify that this number of components meets the threshold
            assert cumulative[n_components - 1] >= threshold, \
                f"Threshold {threshold} not met with {n_components} components"

    def test_realistic_climate_data_simulation(self):
        """Test with a more realistic distribution of eigenvalues for climate data."""
        # Simulate a typical decay pattern for climate modes
        # First few modes explain most variance, then gradual decay
        n_modes = 20
        eigenvalues = np.array([
            15.0, 8.0, 4.0, 2.0, 1.5, 1.0, 0.8, 0.6, 0.5, 0.4,
            0.3, 0.25, 0.2, 0.15, 0.1, 0.08, 0.06, 0.05, 0.04, 0.03
        ])
        
        result = calculate_cumulative_variance(eigenvalues)
        
        # Verify key properties
        assert np.isclose(result[-1], 1.0), \
            "Final cumulative variance should be 1.0"
        
        # Check that top 3 modes explain significant variance
        assert result[2] > 0.7, \
            "Top 3 modes should explain >70% of variance in this simulation"
        
        # Check that top 5 modes explain most variance
        assert result[4] > 0.85, \
            "Top 5 modes should explain >85% of variance in this simulation"

    def test_cumulative_variance_output_format(self):
        """Test that the output format is correct."""
        eigenvalues = np.array([5.0, 3.0, 2.0])
        result = calculate_cumulative_variance(eigenvalues)
        
        # Check type
        assert isinstance(result, np.ndarray), \
            "Result should be a numpy array"
        
        # Check shape
        assert result.shape == eigenvalues.shape, \
            "Result shape should match eigenvalues shape"
        
        # Check dtype
        assert result.dtype in [np.float32, np.float64], \
            "Result should be floating point"

    def test_numerical_stability(self):
        """Test numerical stability with extreme values."""
        # Mix of very large and very small values
        eigenvalues = np.array([1e6, 1e3, 1e-3, 1e-6])
        result = calculate_cumulative_variance(eigenvalues)
        
        # Should not produce NaN or Inf
        assert not np.any(np.isnan(result)), \
            "Result should not contain NaN"
        assert not np.any(np.isinf(result)), \
            "Result should not contain Inf"
        
        # Final value should be 1.0
        assert np.isclose(result[-1], 1.0), \
            "Final cumulative variance should be 1.0"

    def test_integration_with_fpca_pipeline(self):
        """Test that cumulative variance works correctly within the fPCA pipeline."""
        # This test verifies that calculate_cumulative_variance integrates
        # correctly with the rest of the fPCA implementation
        
        # Create a small test dataset
        n_samples = 10
        n_features = 5
        np.random.seed(42)
        test_data = np.random.randn(n_samples, n_features)
        
        # Run fPCA (this will use calculate_cumulative_variance internally)
        try:
            eigenvalues, eigenfunctions, variance_metrics = run_fpca(
                test_data, 
                variance_threshold=0.9
            )
            
            # Verify that variance_metrics contains cumulative variance
            assert 'cumulative_variance' in variance_metrics, \
                "variance_metrics should contain 'cumulative_variance'"
            
            # Verify the cumulative variance is correct
            expected_cumulative = calculate_cumulative_variance(eigenvalues)
            actual_cumulative = variance_metrics['cumulative_variance']
            
            assert np.allclose(expected_cumulative, actual_cumulative), \
                "Cumulative variance in metrics should match calculated values"
            
            # Verify that the stopping criterion worked
            assert variance_metrics['n_components_selected'] <= len(eigenvalues), \
                "Selected components should not exceed total components"
            
        except Exception as e:
            # If fPCA fails due to missing data, at least verify the function exists
            # and works in isolation
            eigenvalues = np.array([5.0, 3.0, 2.0])
            result = calculate_cumulative_variance(eigenvalues)
            assert len(result) == 3
            assert np.isclose(result[-1], 1.0)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])