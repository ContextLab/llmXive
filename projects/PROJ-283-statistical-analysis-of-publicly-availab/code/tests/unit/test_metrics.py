"""
Unit tests for statistical metrics calculations in src/models/metrics.py
"""
import pytest
import numpy as np
import pandas as pd
from src.models.metrics import (
    calculate_wald_z_test,
    calculate_f_statistic,
    calculate_model_f_statistic,
    apply_benjamini_hochberg_fdr,
    calculate_feature_significance
)


class TestWaldZTest:
    def test_basic_wald_test(self):
        """Test basic Wald Z-test calculation"""
        coef = 2.5
        std_err = 0.5
        
        z_stat, p_value = calculate_wald_z_test(coef, std_err)
        
        # z_stat should be coef / std_err
        assert np.isclose(z_stat, 5.0)
        # p_value should be very small for z=5
        assert p_value < 0.0001
        
    def test_zero_std_error(self):
        """Test handling of zero standard error"""
        coef = 2.5
        std_err = 0.0
        
        z_stat, p_value = calculate_wald_z_test(coef, std_err)
        
        assert z_stat == 0.0
        assert p_value == 1.0
        
    def test_nan_std_error(self):
        """Test handling of NaN standard error"""
        coef = 2.5
        std_err = np.nan
        
        z_stat, p_value = calculate_wald_z_test(coef, std_err)
        
        assert z_stat == 0.0
        assert p_value == 1.0
        
    def test_negative_coef(self):
        """Test with negative coefficient"""
        coef = -3.0
        std_err = 0.5
        
        z_stat, p_value = calculate_wald_z_test(coef, std_err)
        
        assert np.isclose(z_stat, -6.0)
        assert p_value < 0.0001


class TestFStatistic:
    def test_f_statistic_comparison(self):
        """Test F-statistic calculation for nested model comparison"""
        rss_restricted = 100.0
        rss_unrestricted = 80.0
        df_restricted = 10
        df_unrestricted = 8
        
        f_stat, p_value = calculate_f_statistic(
            rss_restricted, rss_unrestricted, df_restricted, df_unrestricted
        )
        
        # Manual calculation:
        # numerator = (100 - 80) / (10 - 8) = 20 / 2 = 10
        # denominator = 80 / 8 = 10
        # f_stat = 10 / 10 = 1.0
        assert np.isclose(f_stat, 1.0)
        assert 0 < p_value < 1
        
    def test_zero_unrestricted_rss(self):
        """Test handling of zero unrestricted RSS"""
        rss_restricted = 100.0
        rss_unrestricted = 0.0
        df_restricted = 10
        df_unrestricted = 8
        
        f_stat, p_value = calculate_f_statistic(
            rss_restricted, rss_unrestricted, df_restricted, df_unrestricted
        )
        
        assert np.isinf(f_stat)
        assert p_value == 0.0


class TestModelFStatistic:
    def test_basic_f_statistic(self):
        """Test overall F-statistic calculation from R-squared"""
        r_squared = 0.75
        n_observations = 100
        n_predictors = 5
        
        f_stat, p_value = calculate_model_f_statistic(
            r_squared, n_observations, n_predictors
        )
        
        # Manual calculation:
        # numerator = 0.75 / 5 = 0.15
        # denominator = 0.25 / 94 = 0.00266
        # f_stat = 0.15 / 0.00266 = 56.4
        assert f_stat > 50
        assert p_value < 0.0001
        
    def test_perfect_fit(self):
        """Test with R-squared = 1"""
        r_squared = 1.0
        n_observations = 100
        n_predictors = 5
        
        f_stat, p_value = calculate_model_f_statistic(
            r_squared, n_observations, n_predictors
        )
        
        assert np.isinf(f_stat)
        assert p_value == 0.0
        
    def test_zero_fit(self):
        """Test with R-squared = 0"""
        r_squared = 0.0
        n_observations = 100
        n_predictors = 5
        
        f_stat, p_value = calculate_model_f_statistic(
            r_squared, n_observations, n_predictors
        )
        
        assert f_stat == 0.0
        assert p_value == 1.0


class TestBenjaminiHochberg:
    def test_basic_fdr_correction(self):
        """Test basic Benjamini-Hochberg FDR correction"""
        p_values = [0.01, 0.03, 0.05, 0.1, 0.2]
        
        adj_p_values, rejection_mask = apply_benjamini_hochberg_fdr(p_values, alpha=0.05)
        
        # Adjusted p-values should be >= raw p-values
        for raw, adj in zip(p_values, adj_p_values):
            assert adj >= raw
            
        # First few should be significant at alpha=0.05
        assert rejection_mask[0] == True  # 0.01
        assert rejection_mask[1] == True  # 0.03 (possibly)
        
    def test_empty_list(self):
        """Test with empty p-value list"""
        p_values = []
        
        adj_p_values, rejection_mask = apply_benjamini_hochberg_fdr(p_values)
        
        assert adj_p_values == []
        assert rejection_mask == []
        
    def test_monotonicity(self):
        """Test that adjusted p-values are monotonically non-decreasing"""
        p_values = [0.1, 0.01, 0.05, 0.03]  # Unsorted
        
        adj_p_values, _ = apply_benjamini_hochberg_fdr(p_values)
        
        # Check monotonicity in original order
        for i in range(len(adj_p_values) - 1):
            assert adj_p_values[i] <= adj_p_values[i + 1] or i == len(adj_p_values) - 2
            
    def test_all_significant(self):
        """Test with very small p-values"""
        p_values = [0.001, 0.002, 0.003]
        
        adj_p_values, rejection_mask = apply_benjamini_hochberg_fdr(p_values, alpha=0.05)
        
        # All should be significant
        assert all(rejection_mask)
        
    def test_none_significant(self):
        """Test with large p-values"""
        p_values = [0.5, 0.6, 0.7]
        
        adj_p_values, rejection_mask = apply_benjamini_hochberg_fdr(p_values, alpha=0.05)
        
        # None should be significant
        assert not any(rejection_mask)


class TestFeatureSignificance:
    def test_feature_significance_calculation(self):
        """Test feature significance calculation on synthetic data"""
        # Create synthetic data
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = np.random.randn(n)
        y = 2 * X1 + 0.5 * X2 + np.random.randn(n) * 0.5
        
        df = pd.DataFrame({
            'target': y,
            'feature1': X1,
            'feature2': X2
        })
        
        result = calculate_feature_significance(
            df, 'target', ['feature1', 'feature2']
        )
        
        assert len(result) == 2
        assert 'coefficient' in result.columns
        assert 'p_value' in result.columns
        assert 'adj_p_value' in result.columns
        assert 'is_significant' in result.columns
        
        # feature1 should be significant (coef=2)
        assert result.loc[result['feature'] == 'feature1', 'is_significant'].iloc[0]
        
    def test_empty_dataframe(self):
        """Test with empty dataframe"""
        df = pd.DataFrame()
        
        result = calculate_feature_significance(df, 'target', ['feature1'])
        
        assert len(result) == 0