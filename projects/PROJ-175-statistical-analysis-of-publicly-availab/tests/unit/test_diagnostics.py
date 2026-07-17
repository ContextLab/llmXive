import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LinearRegression

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.diagnostics import calculate_vif, drop_high_vif_predictors

class TestVIFCalculation:
    def test_vif_calculation_simple(self):
        """
        Test VIF calculation on a simple dataset with known collinearity.
        FR-007: Calculate Variance Inflation Factors (VIF) for all predictors.
        """
        # Create data with known collinearity
        # X1 and X2 are highly correlated
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = X1 + 0.1 * np.random.randn(n)  # Highly correlated with X1
        X3 = np.random.randn(n)  # Independent
        
        df = pd.DataFrame({
            'intercept': 1,
            'X1': X1,
            'X2': X2,
            'X3': X3
        })
        
        vif_results = calculate_vif(df, ['X1', 'X2', 'X3'])
        
        # Verify VIF is calculated for all predictors
        assert 'X1' in vif_results
        assert 'X2' in vif_results
        assert 'X3' in vif_results
        
        # X1 and X2 should have high VIF (> 5) due to collinearity
        assert vif_results['X1'] > 5
        assert vif_results['X2'] > 5
        
        # X3 should have low VIF (close to 1)
        assert vif_results['X3'] < 5

    def test_vif_calculation_no_collinearity(self):
        """
        Test VIF calculation on independent predictors.
        """
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = np.random.randn(n)
        X3 = np.random.randn(n)
        
        df = pd.DataFrame({
            'intercept': 1,
            'X1': X1,
            'X2': X2,
            'X3': X3
        })
        
        vif_results = calculate_vif(df, ['X1', 'X2', 'X3'])
        
        # All VIFs should be close to 1 (no collinearity)
        for var in ['X1', 'X2', 'X3']:
            assert 0.5 < vif_results[var] < 2.0

    def test_vif_calculation_perfect_collinearity(self):
        """
        Test VIF calculation with perfect collinearity (should result in very high VIF).
        """
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = X1 * 2  # Perfectly collinear
        X3 = np.random.randn(n)
        
        df = pd.DataFrame({
            'intercept': 1,
            'X1': X1,
            'X2': X2,
            'X3': X3
        })
        
        vif_results = calculate_vif(df, ['X1', 'X2', 'X3'])
        
        # X1 and X2 should have very high VIF
        assert vif_results['X1'] > 100
        assert vif_results['X2'] > 100

class TestDropHighVIFPredictors:
    def test_drop_high_vif_predictors(self):
        """
        Test dropping predictors with VIF > 5.
        FR-007: Drop predictors if VIF > 5.
        """
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = X1 + 0.1 * np.random.randn(n)  # Highly correlated
        X3 = np.random.randn(n)
        X4 = np.random.randn(n)
        
        df = pd.DataFrame({
            'intercept': 1,
            'X1': X1,
            'X2': X2,
            'X3': X3,
            'X4': X4
        })
        
        predictors = ['X1', 'X2', 'X3', 'X4']
        
        # Calculate initial VIFs
        initial_vif = calculate_vif(df, predictors)
        
        # Drop high VIF predictors
        final_predictors, dropped = drop_high_vif_predictors(df, predictors, threshold=5)
        
        # Verify that high VIF predictors were dropped
        assert len(final_predictors) < len(predictors)
        assert 'dropped' in dropped
        assert len(dropped['dropped']) > 0
        
        # Verify that remaining predictors have VIF <= 5
        final_vif = calculate_vif(df, final_predictors)
        for var in final_predictors:
            assert final_vif[var] <= 5.0

    def test_drop_high_vif_predictors_all_good(self):
        """
        Test that no predictors are dropped when all VIFs are low.
        """
        np.random.seed(42)
        n = 100
        X1 = np.random.randn(n)
        X2 = np.random.randn(n)
        X3 = np.random.randn(n)
        
        df = pd.DataFrame({
            'intercept': 1,
            'X1': X1,
            'X2': X2,
            'X3': X3
        })
        
        predictors = ['X1', 'X2', 'X3']
        
        final_predictors, dropped = drop_high_vif_predictors(df, predictors, threshold=5)
        
        # No predictors should be dropped
        assert final_predictors == predictors
        assert len(dropped['dropped']) == 0

    def test_vif_calculation_integration(self):
        """
        Integration test for VIF calculation and dropping logic.
        Verifies FR-007 logic end-to-end.
        """
        # Create a dataset with mixed collinearity
        np.random.seed(42)
        n = 200
        
        # Frequency (main predictor)
        frequency = np.random.uniform(0, 100, n)
        
        # Similarity (moderately correlated with frequency)
        similarity = frequency * 0.3 + np.random.randn(n) * 10
        
        # Role (orthogonalized, should be independent)
        role = np.random.randn(n)
        
        # Co-occurrence (highly correlated with frequency)
        co_occurrence = frequency * 0.9 + np.random.randn(n) * 5
        
        df = pd.DataFrame({
            'intercept': 1,
            'frequency': frequency,
            'similarity': similarity,
            'role': role,
            'co_occurrence': co_occurrence
        })
        
        predictors = ['frequency', 'similarity', 'role', 'co_occurrence']
        
        # Calculate VIFs
        vif_results = calculate_vif(df, predictors)
        
        # Verify VIFs are calculated
        assert len(vif_results) == len(predictors)
        
        # Drop high VIF predictors
        final_predictors, dropped = drop_high_vif_predictors(df, predictors, threshold=5)
        
        # Verify the process worked
        assert isinstance(final_predictors, list)
        assert isinstance(dropped, dict)
        assert 'dropped' in dropped
        assert 'vif_values' in dropped