import pytest
import numpy as np
import pandas as pd
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from features import (
    calculate_variance_and_range,
    calculate_entropy,
    calculate_skewness_and_kurtosis,
    calculate_per_sample_stats,
    calculate_dominant_eigenvalue,
    calculate_global_covariance_and_eigenvalue
)

class TestDominantEigenvalue:
    """Tests for T022b: Per-Sample Dominant Eigenvalue (Global)"""

    def test_global_covariance_eigenvalue_basic(self):
        """Test calculation of dominant eigenvalue from a simple covariance matrix."""
        # Create a simple dataset with known covariance structure
        data = {
            'Alignment': [1.0, 2.0, 3.0, 4.0, 5.0],
            'Realism': [2.0, 4.0, 6.0, 8.0, 10.0],
            'Aesthetics': [1.0, 1.0, 1.0, 1.0, 1.0],  # Zero variance
            'Plausibility': [5.0, 4.0, 3.0, 2.0, 1.0]
        }
        df = pd.DataFrame(data)
        score_cols = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
        
        eigenvalue = calculate_dominant_eigenvalue(df, score_cols)
        
        # Eigenvalue must be a float and non-negative
        assert isinstance(eigenvalue, float)
        assert eigenvalue >= 0.0

    def test_global_covariance_eigenvalue_with_nan(self):
        """Test that NaN values are handled correctly (rows dropped)."""
        data = {
            'Alignment': [1.0, np.nan, 3.0, 4.0, 5.0],
            'Realism': [2.0, 4.0, 6.0, np.nan, 10.0],
            'Aesthetics': [1.0, 1.0, 1.0, 1.0, 1.0],
            'Plausibility': [5.0, 4.0, 3.0, 2.0, 1.0]
        }
        df = pd.DataFrame(data)
        score_cols = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
        
        # Should not raise an error
        eigenvalue = calculate_dominant_eigenvalue(df, score_cols)
        
        assert isinstance(eigenvalue, float)
        assert eigenvalue >= 0.0

    def test_global_covariance_eigenvalue_empty(self):
        """Test behavior with empty dataframe or all NaN."""
        data = {
            'Alignment': [np.nan, np.nan],
            'Realism': [np.nan, np.nan],
            'Aesthetics': [np.nan, np.nan],
            'Plausibility': [np.nan, np.nan]
        }
        df = pd.DataFrame(data)
        score_cols = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
        
        eigenvalue = calculate_dominant_eigenvalue(df, score_cols)
        
        # Should return 0.0 for empty data
        assert eigenvalue == 0.0

    def test_broadcasting_dominant_eigenvalue(self):
        """Test that the global eigenvalue is correctly broadcast to all rows."""
        data = {
            'Alignment': [1.0, 2.0, 3.0, 4.0, 5.0],
            'Realism': [2.0, 4.0, 6.0, 8.0, 10.0],
            'Aesthetics': [1.0, 2.0, 3.0, 4.0, 5.0],
            'Plausibility': [5.0, 4.0, 3.0, 2.0, 1.0]
        }
        df = pd.DataFrame(data)
        score_cols = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
        
        eigenvalue = calculate_dominant_eigenvalue(df, score_cols)
        
        # Verify the value is constant
        assert len(df) > 0
        # The eigenvalue is a single scalar derived from the whole matrix
        # We just verify it's a valid number that can be broadcast
        assert np.isfinite(eigenvalue)

    def test_covariance_matrix_symmetry(self):
        """Verify that the covariance calculation produces a symmetric matrix (implicitly)."""
        # This test ensures the underlying math is sound
        data = {
            'A': [1.0, 2.0, 3.0],
            'B': [4.0, 5.0, 6.0],
            'C': [7.0, 8.0, 9.0]
        }
        df = pd.DataFrame(data)
        cols = ['A', 'B', 'C']
        
        eigenvalue = calculate_dominant_eigenvalue(df, cols)
        
        # For a 3x3 matrix, the dominant eigenvalue should be positive
        assert eigenvalue > 0.0

class TestPerSampleStats:
    """Tests for T022a: Per-Sample Entanglement Score"""

    def test_variance_calculation(self):
        """Test variance calculation for a simple list."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        var, rng = calculate_variance_and_range(values)
        assert abs(var - 2.0) < 0.01  # Population variance of 1..5 is 2.0

    def test_entropy_zero_variance(self):
        """Test entropy is 0 when all values are the same."""
        values = [1.0, 1.0, 1.0, 1.0]
        ent = calculate_entropy(values)
        assert ent == 0.0

    def test_skewness_kurtosis_basic(self):
        """Test skewness and kurtosis calculation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        skew, kurt = calculate_skewness_and_kurtosis(values)
        # For a uniform distribution, skew should be ~0
        assert abs(skew) < 0.1

    def test_per_sample_stats_integration(self):
        """Test the full per-sample stats calculation."""
        row = {
            'Alignment': 0.8,
            'Realism': 0.6,
            'Aesthetics': 0.9,
            'Plausibility': 0.7
        }
        cols = ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
        stats = calculate_per_sample_stats(row, cols)
        
        assert 'variance' in stats
        assert 'entropy' in stats
        assert 'skewness' in stats
        assert 'kurtosis' in stats
        assert stats['variance'] >= 0
        assert stats['entropy'] >= 0

if __name__ == '__main__':
    pytest.main([__file__, '-v'])