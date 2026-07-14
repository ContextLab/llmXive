"""
Unit tests for metrics calculation functions.
"""
import pytest
import numpy as np
from scipy import stats
from src.models.metrics import (
    calculate_wald_z_statistic,
    calculate_p_value_z_test,
    calculate_f_statistic,
    apply_benjamini_hochberg_fdr,
    calculate_metric_summary
)


class TestWaldZStatistic:
    """Tests for Wald Z-statistic calculation."""
    
    def test_basic_calculation(self):
        """Test basic Z-statistic calculation."""
        coef = 2.5
        se = 0.5
        expected_z = 5.0
        
        result = calculate_wald_z_statistic(coef, se)
        assert abs(result - expected_z) < 1e-10
    
    def test_negative_coefficient(self):
        """Test Z-statistic with negative coefficient."""
        coef = -3.0
        se = 1.0
        expected_z = -3.0
        
        result = calculate_wald_z_statistic(coef, se)
        assert abs(result - expected_z) < 1e-10
    
    def test_small_standard_error(self):
        """Test Z-statistic with small standard error."""
        coef = 1.0
        se = 0.01
        expected_z = 100.0
        
        result = calculate_wald_z_statistic(coef, se)
        assert abs(result - expected_z) < 1e-6
    
    def test_zero_standard_error_raises_error(self):
        """Test that zero standard error raises ValueError."""
        with pytest.raises(ValueError):
            calculate_wald_z_statistic(1.0, 0.0)
    
    def test_negative_standard_error_raises_error(self):
        """Test that negative standard error raises ValueError."""
        with pytest.raises(ValueError):
            calculate_wald_z_statistic(1.0, -0.5)


class TestPValueZTest:
    """Tests for p-value calculation from Z-statistic."""
    
    def test_zero_z_statistic(self):
        """Test p-value for Z=0 should be 1.0."""
        result = calculate_p_value_z_test(0.0)
        assert abs(result - 1.0) < 1e-10
    
    def test_large_positive_z(self):
        """Test p-value for large positive Z should be small."""
        result = calculate_p_value_z_test(5.0)
        assert result < 0.0001
    
    def test_large_negative_z(self):
        """Test p-value for large negative Z should be small."""
        result = calculate_p_value_z_test(-5.0)
        assert result < 0.0001
    
    def test_symmetry(self):
        """Test that p-values are symmetric for positive and negative Z."""
        z_pos = 2.0
        z_neg = -2.0
        
        p_pos = calculate_p_value_z_test(z_pos)
        p_neg = calculate_p_value_z_test(z_neg)
        
        assert abs(p_pos - p_neg) < 1e-10
    
    def test_z_equals_196(self):
        """Test p-value for Z=1.96 should be approximately 0.05."""
        result = calculate_p_value_z_test(1.96)
        assert abs(result - 0.05) < 0.01


class TestFStatistic:
    """Tests for F-statistic calculation."""
    
    def test_basic_calculation(self):
        """Test basic F-statistic calculation."""
        r_squared = 0.5
        n_samples = 100
        n_predictors = 5
        
        # F = (R²/k) / ((1-R²)/(n-k-1))
        # F = (0.5/5) / (0.5/94) = 0.1 / 0.005319 = 18.8
        expected_f = (r_squared / n_predictors) / ((1 - r_squared) / (n_samples - n_predictors - 1))
        
        result = calculate_f_statistic(r_squared, n_samples, n_predictors)
        assert abs(result - expected_f) < 1e-6
    
    def test_perfect_fit(self):
        """Test F-statistic with perfect fit (R²=1)."""
        r_squared = 1.0
        n_samples = 100
        n_predictors = 5
        
        result = calculate_f_statistic(r_squared, n_samples, n_predictors)
        assert result == float('inf')
    
    def test_zero_r_squared(self):
        """Test F-statistic with R²=0."""
        r_squared = 0.0
        n_samples = 100
        n_predictors = 5
        
        result = calculate_f_statistic(r_squared, n_samples, n_predictors)
        assert result == 0.0
    
    def test_insufficient_samples(self):
        """Test F-statistic with insufficient samples."""
        r_squared = 0.5
        n_samples = 5
        n_predictors = 5
        
        result = calculate_f_statistic(r_squared, n_samples, n_predictors)
        assert result == 0.0


class TestBenjaminiHochbergFDR:
    """Tests for Benjamini-Hochberg FDR correction."""
    
    def test_empty_array(self):
        """Test FDR correction with empty array."""
        result = apply_benjamini_hochberg_fdr(np.array([]))
        assert len(result) == 0
    
    def test_single_p_value(self):
        """Test FDR correction with single p-value."""
        p_values = np.array([0.05])
        result = apply_benjamini_hochberg_fdr(p_values)
        # For single value, adjusted = raw
        assert abs(result[0] - 0.05) < 1e-10
    
    def test_monotonicity(self):
        """Test that adjusted p-values maintain monotonicity."""
        p_values = np.array([0.1, 0.05, 0.01, 0.2, 0.03])
        result = apply_benjamini_hochberg_fdr(p_values)
        
        # Find indices where original p-values were sorted
        sorted_indices = np.argsort(p_values)
        sorted_adjusted = result[sorted_indices]
        
        # Check that adjusted p-values are monotonically increasing
        for i in range(len(sorted_adjusted) - 1):
            assert sorted_adjusted[i] <= sorted_adjusted[i + 1]
    
    def test_clamping(self):
        """Test that adjusted p-values are clamped to [0, 1]."""
        p_values = np.array([0.5, 0.6, 0.7, 0.8, 0.9])
        result = apply_benjamini_hochberg_fdr(p_values)
        
        assert np.all(result >= 0)
        assert np.all(result <= 1)
    
    def test_known_example(self):
        """Test FDR correction with a known example."""
        # Example from Benjamini-Hochberg paper
        p_values = np.array([0.001, 0.004, 0.009, 0.015, 0.022, 0.028, 0.031, 0.035, 0.041, 0.050])
        result = apply_benjamini_hochberg_fdr(p_values)
        
        # All adjusted p-values should be >= corresponding raw p-values
        assert np.all(result >= p_values)


class TestMetricSummary:
    """Tests for comprehensive metrics summary calculation."""
    
    def test_basic_summary(self):
        """Test basic metrics summary calculation."""
        model_results = {
            'coefficients': np.array([1.0, 2.0, 3.0]),
            'standard_errors': np.array([0.5, 0.5, 0.5]),
            'r_squared': 0.6,
            'n_samples': 100,
            'n_predictors': 3
        }
        
        result = calculate_metric_summary(model_results)
        
        assert 'z_statistics' in result
        assert 'p_values' in result
        assert 'adjusted_p_values' in result
        assert 'f_statistic' in result
        assert 'r_squared' in result
        assert 'n_samples' in result
        assert 'n_predictors' in result
        
        assert len(result['z_statistics']) == 3
        assert len(result['p_values']) == 3
        assert len(result['adjusted_p_values']) == 3
    
    def test_nan_handling(self):
        """Test handling of invalid standard errors."""
        model_results = {
            'coefficients': np.array([1.0, 2.0, 3.0]),
            'standard_errors': np.array([0.5, 0.0, 0.5]),  # Zero SE should cause NaN
            'r_squared': 0.6,
            'n_samples': 100,
            'n_predictors': 3
        }
        
        result = calculate_metric_summary(model_results)
        
        # First and third should be valid, second should be NaN
        assert not np.isnan(result['z_statistics'][0])
        assert np.isnan(result['z_statistics'][1])
        assert not np.isnan(result['z_statistics'][2])
    
    def test_f_statistic_calculation(self):
        """Test that F-statistic is calculated correctly in summary."""
        model_results = {
            'coefficients': np.array([1.0, 2.0]),
            'standard_errors': np.array([0.5, 0.5]),
            'r_squared': 0.5,
            'n_samples': 100,
            'n_predictors': 2
        }
        
        result = calculate_metric_summary(model_results)
        
        # Expected F = (0.5/2) / (0.5/97) = 0.25 / 0.00515 = 48.5
        expected_f = (0.5 / 2) / ((1 - 0.5) / (100 - 2 - 1))
        assert abs(result['f_statistic'] - expected_f) < 1e-6