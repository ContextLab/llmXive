import pytest
import pandas as pd
import numpy as np
from src.data.features import (
    calculate_elemental_ratios,
    calculate_pairwise_interactions,
    orthogonalize_spline,
    orthogonalize_interactions,
    detect_zero_variance_columns,
    exclude_collinear_thermal_features,
    engineer_features
)

class TestElementalRatios:
    def test_calculate_ratios(self):
        df = pd.DataFrame({
            'C': [0.1, 0.2],
            'Mn': [1.0, 2.0],
            'Cr': [5.0, 10.0],
            'Ni': [2.0, 4.0]
        })
        result = calculate_elemental_ratios(df)
        assert 'C_Mn_ratio' in result.columns
        assert 'Cr_Ni_ratio' in result.columns
        # Check values
        assert np.isclose(result['C_Mn_ratio'][0], 0.1)
        assert np.isclose(result['Cr_Ni_ratio'][0], 2.5)

class TestPairwiseInteractions:
    def test_calculate_interactions(self):
        df = pd.DataFrame({
            'cooling_rate': [10.0, 20.0],
            'holding_time': [5.0, 10.0],
            'C': [0.1, 0.2]
        })
        result = calculate_pairwise_interactions(df)
        assert 'cooling_rate_x_holding_time' in result.columns
        assert 'C_x_cooling_rate' in result.columns
        assert np.isclose(result['cooling_rate_x_holding_time'][0], 50.0)
        assert np.isclose(result['C_x_cooling_rate'][0], 1.0)

class TestOrthogonalizeSpline:
    def test_orthogonalize_spline_linear(self):
        # Create data where interaction is perfectly linear combination of main effects
        # y = x1 + x2
        # Interaction term should be orthogonalized to 0 (or near 0)
        x1 = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        x2 = pd.Series([2.0, 4.0, 6.0, 8.0, 10.0])
        interaction = x1 * x2 # This is not linear, but let's test the function
        
        # Actually, let's test with a case where interaction is linearly dependent
        # y = 2*x1 + 3*x2
        # We want to orthogonalize y against x1, x2
        # The residual should be 0 (or near 0)
        
        # Let's create a simpler case:
        # interaction = x1 + x2
        # We want to orthogonalize interaction against x1, x2
        # The residual should be 0
        interaction = x1 + x2
        result = orthogonalize_spline(interaction, [x1, x2], degree=3, knots=5)
        # The residuals should be close to 0
        assert np.allclose(result.values, 0.0, atol=1e-5)

    def test_orthogonalize_spline_nonlinear(self):
        # Test with a non-linear relationship
        x1 = pd.Series(np.linspace(0, 10, 100))
        x2 = pd.Series(np.linspace(0, 10, 100))
        # interaction = x1^2 + x2^2
        interaction = x1**2 + x2**2
        result = orthogonalize_spline(interaction, [x1, x2], degree=3, knots=5)
        # The residuals should not be all zero (since x^2 is not linear)
        # But the variance explained by linear terms should be removed
        assert np.std(result) > 0

class TestZeroVariance:
    def test_detect_zero_variance(self):
        df = pd.DataFrame({
            'const': [5.0, 5.0, 5.0],
            'var': [1.0, 2.0, 3.0]
        })
        result = detect_zero_variance_columns(df)
        assert 'const' in result
        assert 'var' not in result

class TestEngineerFeatures:
    def test_full_pipeline(self):
        df = pd.DataFrame({
            'C': [0.1, 0.2, 0.3],
            'Mn': [1.0, 2.0, 3.0],
            'cooling_rate': [10.0, 20.0, 30.0],
            'holding_time': [5.0, 10.0, 15.0],
            'yield_strength': [500.0, 600.0, 700.0]
        })
        result = engineer_features(df)
        # Check that new columns are added
        assert 'C_Mn_ratio' in result.columns
        assert 'cooling_rate_x_holding_time' in result.columns
        # Check that orthogonalization happened (columns exist)
        assert 'cooling_rate_x_holding_time' in result.columns
        # Check no NaNs in target (if present)
        if 'yield_strength' in result.columns:
            assert not result['yield_strength'].isna().any()