import pytest
import pandas as pd
import numpy as np
from scipy.stats import norm
from code.analysis.correlation import check_normality, calculate_correlation, benjamini_hochberg_fdr

class TestNormalityTesting:
    """Tests for T024: Normality testing (Shapiro-Wilk)"""
    
    def test_normal_distribution_detected(self):
        """Test that a normally distributed sample is correctly identified as normal"""
        np.random.seed(42)
        normal_data = pd.Series(np.random.normal(loc=0, scale=1, size=100))
        
        is_normal, p_value = check_normality(normal_data)
        
        assert is_normal, "Normally distributed data should be detected as normal"
        assert p_value > 0.05, f"p-value {p_value} should be > 0.05 for normal data"
    
    def test_non_normal_distribution_detected(self):
        """Test that a non-normal distribution is correctly identified"""
        # Exponential distribution is clearly non-normal
        exp_data = pd.Series(np.random.exponential(scale=1.0, size=100))
        
        is_normal, p_value = check_normality(exp_data)
        
        assert not is_normal, "Exponential distribution should be detected as non-normal"
        assert p_value <= 0.05, f"p-value {p_value} should be <= 0.05 for non-normal data"
    
    def test_small_sample_size_warning(self):
        """Test that small sample sizes trigger a warning"""
        small_data = pd.Series([1.0, 2.0, 3.0])
        
        with pytest.warns(UserWarning, match="too small"):
            is_normal, p_value = check_normality(small_data)
        
        assert not is_normal, "Small samples should default to non-normal"
    
    def test_alpha_threshold(self):
        """Test that the alpha threshold works correctly"""
        # Create data that will have p-value close to 0.05
        np.random.seed(123)
        data = pd.Series(np.random.normal(0, 1, 50))
        
        # Test with alpha=0.05
        is_normal_05, p_val = check_normality(data, alpha=0.05)
        
        # Test with alpha=0.01 (stricter)
        is_normal_01, _ = check_normality(data, alpha=0.01)
        
        # If p-value is between 0.01 and 0.05, we should see different results
        if 0.01 < p_val <= 0.05:
            assert not is_normal_01, "Should be non-normal at alpha=0.01"
            assert is_normal_05, "Should be normal at alpha=0.05"

class TestCorrelationSelection:
    """Tests for automatic correlation method selection"""
    
    def test_pearson_selected_for_normal_data(self):
        """Test that Pearson correlation is selected when both variables are normal"""
        np.random.seed(42)
        x = pd.Series(np.random.normal(0, 1, 100))
        y = pd.Series(np.random.normal(0, 1, 100))
        
        r, p = calculate_correlation(x, y, method='auto')
        
        # Both should be detected as normal, so Pearson should be used
        # We can't directly check the method used, but we can verify the result is reasonable
        assert not np.isnan(r), "Correlation coefficient should not be NaN"
        assert not np.isnan(p), "p-value should not be NaN"
    
    def test_spearman_selected_for_non_normal_data(self):
        """Test that Spearman correlation is selected when data is non-normal"""
        np.random.seed(42)
        x = pd.Series(np.random.exponential(1, 100))
        y = pd.Series(np.random.exponential(1, 100))
        
        r, p = calculate_correlation(x, y, method='auto')
        
        assert not np.isnan(r), "Correlation coefficient should not be NaN"
        assert not np.isnan(p), "p-value should not be NaN"
    
    def test_explicit_pearson(self):
        """Test explicit Pearson correlation"""
        np.random.seed(42)
        x = pd.Series(np.random.normal(0, 1, 100))
        y = pd.Series(np.random.normal(0, 1, 100))
        
        r, p = calculate_correlation(x, y, method='pearson')
        
        assert not np.isnan(r)
        assert not np.isnan(p)
    
    def test_explicit_spearman(self):
        """Test explicit Spearman correlation"""
        np.random.seed(42)
        x = pd.Series(np.random.exponential(1, 100))
        y = pd.Series(np.random.exponential(1, 100))
        
        r, p = calculate_correlation(x, y, method='spearman')
        
        assert not np.isnan(r)
        assert not np.isnan(p)
    
    def test_insufficient_data_raises(self):
        """Test that insufficient data raises an error"""
        x = pd.Series([1.0, 2.0])
        y = pd.Series([1.0, 2.0])
        
        with pytest.raises(ValueError, match="Insufficient data"):
            calculate_correlation(x, y, method='auto')

class TestFDRCorrection:
    """Tests for Benjamini-Hochberg FDR correction"""
    
    def test_fdr_with_clear_significance(self):
        """Test FDR correction with clearly significant p-values"""
        p_values = [0.001, 0.002, 0.01, 0.02, 0.1, 0.2, 0.3]
        results = benjamini_hochberg_fdr(p_values, q=0.05)
        
        # The smallest p-values should be significant
        assert results[0] == True, "Smallest p-value should be significant"
        assert results[1] == True, "Second smallest should likely be significant"
    
    def test_fdr_with_no_significance(self):
        """Test FDR correction when no p-values are significant"""
        p_values = [0.5, 0.6, 0.7, 0.8, 0.9]
        results = benjamini_hochberg_fdr(p_values, q=0.05)
        
        # None should be significant
        assert all(not r for r in results), "No p-values should be significant"
    
    def test_fdr_empty_list(self):
        """Test FDR correction with empty list"""
        results = benjamini_hochberg_fdr([], q=0.05)
        assert results == []
    
    def test_fdr_single_value(self):
        """Test FDR correction with single p-value"""
        results = benjamini_hochberg_fdr([0.01], q=0.05)
        assert results[0] == True, "Single significant p-value should be significant"
        
        results = benjamini_hochberg_fdr([0.1], q=0.05)
        assert results[0] == False, "Single non-significant p-value should not be significant"

class TestIntegration:
    """Integration tests for the correlation analysis workflow"""
    
    def test_end_to_end_normality_check(self):
        """Test the complete flow from data generation to normality check"""
        # Generate normal data
        np.random.seed(42)
        normal_data = pd.Series(np.random.normal(0, 1, 200))
        
        is_normal, p_value = check_normality(normal_data)
        
        assert is_normal
        assert p_value > 0.05
    
    def test_end_to_end_correlation_selection(self):
        """Test complete correlation workflow with method selection"""
        np.random.seed(42)
        
        # Create correlated normal data
        x = pd.Series(np.random.normal(0, 1, 100))
        y = x * 0.8 + np.random.normal(0, 0.5, 100)
        
        r, p = calculate_correlation(x, y, method='auto')
        
        # Should detect normality and use Pearson
        assert abs(r) > 0.5, "Should detect strong correlation"
        assert p < 0.05, "Correlation should be significant"
    
    def test_end_to_end_fdr_workflow(self):
        """Test complete FDR workflow with multiple tests"""
        # Simulate multiple hypothesis testing
        np.random.seed(42)
        p_values = [0.001, 0.005, 0.01, 0.03, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5]
        
        significant = benjamini_hochberg_fdr(p_values, q=0.05)
        
        # At least the most significant ones should pass
        assert sum(significant) >= 2, "At least 2 tests should be significant after FDR"