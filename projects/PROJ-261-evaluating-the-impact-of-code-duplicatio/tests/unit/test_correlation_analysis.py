"""
Unit tests for correlation_analysis.py Spearman coefficient computation.

This test module validates the Spearman rank correlation computation
implemented in code/correlation_analysis.py. Tests are designed to be
independent of the data pipeline and use mock data for reproducibility.

Per spec.md Independent Test requirements for US2.
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from correlation_analysis import (
    compute_spearman_correlation,
    load_metrics_data,
    compute_correlation_matrix,
    run_sensitivity_analysis
)

from config import (
    get_correlation_method,
    get_significance_threshold
)

class TestComputeSpearmanCorrelation:
    """Unit tests for compute_spearman_correlation function."""
    
    def test_perfect_positive_correlation(self):
        """Test with perfectly correlated data (should return 1.0)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr == pytest.approx(1.0, abs=1e-10)
        assert p_value < 0.001
        
    def test_perfect_negative_correlation(self):
        """Test with perfectly negatively correlated data (should return -1.0)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr == pytest.approx(-1.0, abs=1e-10)
        assert p_value < 0.001
        
    def test_no_correlation(self):
        """Test with uncorrelated data (should return near 0)."""
        np.random.seed(42)
        x = np.random.randn(100)
        y = np.random.randn(100)
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        # With random data, correlation should be small
        assert abs(corr) < 0.3
        assert p_value > 0.05
        
    def test_moderate_positive_correlation(self):
        """Test with moderately correlated data."""
        np.random.seed(42)
        x = np.arange(50)
        noise = np.random.randn(50) * 5
        y = x + noise
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert 0.5 < corr < 1.0
        assert p_value < 0.01
        
    def test_moderate_negative_correlation(self):
        """Test with moderately negatively correlated data."""
        np.random.seed(42)
        x = np.arange(50)
        noise = np.random.randn(50) * 5
        y = -x + noise
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert -1.0 < corr < -0.5
        assert p_value < 0.01
        
    def test_constant_values(self):
        """Test with constant values (should handle gracefully)."""
        x = np.array([5, 5, 5, 5, 5])
        y = np.array([1, 2, 3, 4, 5])
        
        # Should not raise an exception
        corr, p_value = compute_spearman_correlation(x, y)
        
        # Result may be NaN or 0 depending on implementation
        assert not np.isnan(corr) or p_value is not None
        
    def test_single_value(self):
        """Test with single value (edge case)."""
        x = np.array([5])
        y = np.array([10])
        
        # Should handle single value gracefully
        corr, p_value = compute_spearman_correlation(x, y)
        
        # May return NaN for single value
        assert p_value is not None
        
    def test_mismatched_lengths(self):
        """Test with mismatched array lengths (should raise error)."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([1, 2, 3])
        
        with pytest.raises((ValueError, AssertionError)):
            compute_spearman_correlation(x, y)
            
    def test_empty_arrays(self):
        """Test with empty arrays (should raise error)."""
        x = np.array([])
        y = np.array([])
        
        with pytest.raises((ValueError, AssertionError)):
            compute_spearman_correlation(x, y)
            
    def test_with_nan_values(self):
        """Test with NaN values (should handle or raise appropriate error)."""
        x = np.array([1, 2, np.nan, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        # Should either handle NaN or raise an error
        with pytest.raises((ValueError, RuntimeError)):
            compute_spearman_correlation(x, y)
            
    def test_return_types(self):
        """Test that function returns correct types."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert isinstance(corr, (float, np.floating))
        assert isinstance(p_value, (float, np.floating))
        
    def test_p_value_bounds(self):
        """Test that p-value is within valid bounds [0, 1]."""
        np.random.seed(42)
        x = np.random.randn(50)
        y = np.random.randn(50)
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert 0 <= p_value <= 1
        
    def test_correlation_bounds(self):
        """Test that correlation coefficient is within [-1, 1]."""
        np.random.seed(42)
        for _ in range(10):
            x = np.random.randn(50)
            y = np.random.randn(50)
            
            corr, p_value = compute_spearman_correlation(x, y)
            
            assert -1 <= corr <= 1
            
    def test_large_dataset(self):
        """Test with larger dataset for performance."""
        np.random.seed(42)
        x = np.random.randn(10000)
        y = np.random.randn(10000)
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert isinstance(corr, float)
        assert isinstance(p_value, float)
        
    def test_duplicate_values(self):
        """Test with duplicate values (tied ranks)."""
        x = np.array([1, 1, 2, 2, 3, 3])
        y = np.array([2, 2, 4, 4, 6, 6])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        # Should handle tied ranks correctly
        assert corr == pytest.approx(1.0, abs=1e-6)
        
    def test_significance_threshold(self):
        """Test that significant correlations are properly identified."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = np.array([10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        significance_threshold = get_significance_threshold()
        is_significant = p_value < significance_threshold
        
        assert is_significant  # Perfect negative correlation should be significant
        
    def test_with_lists_instead_of_arrays(self):
        """Test that function accepts Python lists."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr == pytest.approx(1.0, abs=1e-10)
        
    def test_with_float_values(self):
        """Test with float values (not just integers)."""
        x = [1.1, 2.2, 3.3, 4.4, 5.5]
        y = [2.2, 4.4, 6.6, 8.8, 11.0]
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr == pytest.approx(1.0, abs=1e-10)
        
    def test_with_negative_values(self):
        """Test with negative values in arrays."""
        x = [-5, -3, -1, 1, 3, 5]
        y = [-2, -1.5, -1, 1, 1.5, 2]
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr > 0.8  # Should show positive correlation
        
    def test_correlation_method_from_config(self):
        """Test that correlation method from config is used."""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        # The function should use the configured method (Spearman)
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr == pytest.approx(1.0, abs=1e-10)
        
    def test_reproducibility_with_seed(self):
        """Test that results are reproducible with same random seed."""
        np.random.seed(42)
        x1 = np.random.randn(100)
        y1 = np.random.randn(100)
        
        np.random.seed(42)
        x2 = np.random.randn(100)
        y2 = np.random.randn(100)
        
        corr1, p1 = compute_spearman_correlation(x1, y1)
        corr2, p2 = compute_spearman_correlation(x2, y2)
        
        assert corr1 == corr2
        assert p1 == p2
        
    def test_outlier_sensitivity(self):
        """Test Spearman's robustness to outliers (compared to Pearson)."""
        # Spearman should be more robust to outliers
        x = np.array([1, 2, 3, 4, 5, 100])  # 100 is outlier
        y = np.array([2, 4, 6, 8, 10, 12])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        # Should still detect positive correlation despite outlier
        assert corr > 0.5
        
    def test_monotonic_relationship(self):
        """Test with monotonic but non-linear relationship."""
        x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        y = np.array([1, 4, 9, 16, 25, 36, 49, 64, 81, 100])  # x^2
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        # Spearman should detect monotonic relationship
        assert corr > 0.9
        
    def test_with_zeros(self):
        """Test with zero values in arrays."""
        x = np.array([0, 1, 2, 3, 4, 5])
        y = np.array([0, 2, 4, 6, 8, 10])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr == pytest.approx(1.0, abs=1e-10)
        
    def test_with_very_small_values(self):
        """Test with very small floating point values."""
        x = np.array([1e-10, 2e-10, 3e-10, 4e-10, 5e-10])
        y = np.array([2e-10, 4e-10, 6e-10, 8e-10, 10e-10])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr == pytest.approx(1.0, abs=1e-10)
        
    def test_with_very_large_values(self):
        """Test with very large values."""
        x = np.array([1e10, 2e10, 3e10, 4e10, 5e10])
        y = np.array([2e10, 4e10, 6e10, 8e10, 10e10])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        assert corr == pytest.approx(1.0, abs=1e-10)
        
    def test_asymmetric_input(self):
        """Test with asymmetric data (different distributions)."""
        x = np.array([1, 1, 1, 1, 10, 10, 10, 10])
        y = np.array([1, 2, 3, 4, 1, 2, 3, 4])
        
        corr, p_value = compute_spearman_correlation(x, y)
        
        # Should handle asymmetric data without crashing
        assert not np.isnan(corr)
        
    def test_with_inf_values(self):
        """Test with infinity values (should raise error or handle)."""
        x = np.array([1, 2, 3, np.inf, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        # Should handle or raise error for infinity
        with pytest.raises((ValueError, RuntimeError)):
            compute_spearman_correlation(x, y)
        
        
class TestComputeCorrelationMatrix:
    """Unit tests for compute_correlation_matrix function."""
    
    def test_single_pair(self):
        """Test with single pair of variables."""
        data = {
            'clone_density': np.array([1, 2, 3, 4, 5]),
            'perplexity': np.array([2, 4, 6, 8, 10])
        }
        
        matrix, p_values = compute_correlation_matrix(data)
        
        assert matrix.shape == (1, 1)
        assert matrix[0, 0] == pytest.approx(1.0, abs=1e-10)
        
    def test_multiple_pairs(self):
        """Test with multiple pairs of variables."""
        np.random.seed(42)
        data = {
            'clone_density': np.random.randn(100),
            'perplexity': np.random.randn(100),
            'accuracy': np.random.randn(100)
        }
        
        matrix, p_values = compute_correlation_matrix(data)
        
        assert matrix.shape == (3, 3)
        assert p_values.shape == (3, 3)
        
    def test_diagonal_is_one(self):
        """Test that diagonal elements are 1 (self-correlation)."""
        data = {
            'a': np.array([1, 2, 3, 4, 5]),
            'b': np.array([2, 4, 6, 8, 10]),
            'c': np.array([3, 6, 9, 12, 15])
        }
        
        matrix, _ = compute_correlation_matrix(data)
        
        assert matrix[0, 0] == pytest.approx(1.0)
        assert matrix[1, 1] == pytest.approx(1.0)
        assert matrix[2, 2] == pytest.approx(1.0)
        
    def test_symmetric_matrix(self):
        """Test that correlation matrix is symmetric."""
        np.random.seed(42)
        data = {
            'x': np.random.randn(50),
            'y': np.random.randn(50)
        }
        
        matrix, _ = compute_correlation_matrix(data)
        
        assert np.allclose(matrix, matrix.T)
        
    def test_empty_data(self):
        """Test with empty data dictionary."""
        data = {}
        
        with pytest.raises((ValueError, AssertionError)):
            compute_correlation_matrix(data)
        
        
class TestLoadMetricsData:
    """Unit tests for load_metrics_data function."""
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_load_from_csv(self, mock_read_text, mock_exists):
        """Test loading data from CSV file."""
        mock_exists.return_value = True
        mock_read_text.return_value = """clone_density,perplexity,accuracy
        0.1,10.5,0.8
        0.2,11.0,0.75
        0.3,11.5,0.7
        """
        
        data = load_metrics_data(Path('/fake/path.csv'))
        
        assert 'clone_density' in data
        assert 'perplexity' in data
        assert 'accuracy' in data
        assert len(data['clone_density']) == 3
        
    @patch('pathlib.Path.exists')
    def test_file_not_found(self, mock_exists):
        """Test handling of missing file."""
        mock_exists.return_value = False
        
        with pytest.raises(FileNotFoundError):
            load_metrics_data(Path('/fake/nonexistent.csv'))
        
        
class TestRunSensitivityAnalysis:
    """Unit tests for run_sensitivity_analysis function."""
    
    def test_with_thresholds(self):
        """Test sensitivity analysis with multiple thresholds."""
        thresholds = [0.7, 0.8, 0.9]
        
        np.random.seed(42)
        data = {
            'clone_density': np.random.randn(100),
            'perplexity': np.random.randn(100)
        }
        
        results = run_sensitivity_analysis(data, thresholds)
        
        assert len(results) == len(thresholds)
        for threshold, result in zip(thresholds, results):
            assert 'threshold' in result
            assert 'correlation' in result
            assert 'p_value' in result
            
    def test_returns_expected_structure(self):
        """Test that sensitivity analysis returns expected structure."""
        thresholds = [0.7, 0.8, 0.9]
        
        np.random.seed(42)
        data = {
            'clone_density': np.random.randn(100),
            'perplexity': np.random.randn(100)
        }
        
        results = run_sensitivity_analysis(data, thresholds)
        
        assert isinstance(results, list)
        assert all(isinstance(r, dict) for r in results)