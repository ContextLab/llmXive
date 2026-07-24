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
    def test_calculate_elemental_ratios(self):
        df = pd.DataFrame({
            'C': [0.1, 0.2, 0.3],
            'Mn': [1.0, 2.0, 3.0],
            'Cr': [10.0, 20.0, 30.0],
            'Ni': [5.0, 10.0, 15.0]
        })
        result = calculate_elemental_ratios(df)
        assert 'C_Mn_ratio' in result.columns
        assert 'Cr_Ni_ratio' in result.columns
        assert np.isclose(result['C_Mn_ratio'].iloc[0], 0.1)
        assert np.isclose(result['Cr_Ni_ratio'].iloc[0], 2.0)

class TestPairwiseInteractions:
    def test_calculate_pairwise_interactions(self):
        df = pd.DataFrame({
            'cooling_rate_norm': [0.1, 0.2, 0.3],
            'holding_time_norm': [0.5, 0.6, 0.7],
            'C': [0.1, 0.2, 0.3]
        })
        result = calculate_pairwise_interactions(df)
        assert 'cooling_rate_x_holding_time' in result.columns
        assert 'C_x_cooling_rate' in result.columns
        assert np.isclose(result['cooling_rate_x_holding_time'].iloc[0], 0.05)
        assert np.isclose(result['C_x_cooling_rate'].iloc[0], 0.01)

class TestOrthogonalizeSpline:
    def test_orthogonalize_spline_basic(self):
        x = np.linspace(0, 10, 100)
        y = 2 * x + np.random.normal(0, 0.1, 100)
        residuals = orthogonalize_spline(x, y)
        # Residuals should have mean close to 0
        assert np.abs(np.mean(residuals)) < 0.1

class TestZeroVariance:
    def test_detect_zero_variance_columns(self):
        df = pd.DataFrame({
            'zero_var': [1, 1, 1],
            'normal_var': [1, 2, 3],
            'nan_var': [np.nan, np.nan, np.nan]
        })
        cols = detect_zero_variance_columns(df)
        assert 'zero_var' in cols
        assert 'nan_var' in cols
        assert 'normal_var' not in cols

    def test_exclude_collinear_thermal_features(self):
        df = pd.DataFrame({
            'temp_norm': [1.0, 1.0, 1.0], # Zero variance
            'cooling_rate_norm': [0.1, 0.2, 0.3],
            'other_feature': [1, 2, 3]
        })
        result = exclude_collinear_thermal_features(df)
        assert 'temp_norm' not in result.columns
        assert 'cooling_rate_norm' in result.columns

class TestEngineerFeatures:
    def test_engineer_features_pipeline(self):
        df = pd.DataFrame({
            'C': [0.1, 0.2],
            'Mn': [1.0, 2.0],
            'Cr': [10.0, 20.0],
            'Ni': [5.0, 10.0],
            'cooling_rate_norm': [0.1, 0.2],
            'holding_time_norm': [0.5, 0.6],
            'temp_norm': [1.0, 1.0] # Zero variance thermal feature
        })
        result = engineer_features(df)
        # Should have ratios
        assert 'C_Mn_ratio' in result.columns
        # Should have interactions
        assert 'cooling_rate_x_holding_time' in result.columns
        # Should have orthogonalized interactions
        assert 'cooling_rate_x_holding_time_orthogonalized' in result.columns
        # Should NOT have zero variance thermal feature
        assert 'temp_norm' not in result.columns
        # Should have other features
        assert 'cooling_rate_norm' in result.columns
        assert 'other_feature' not in result.columns # Wait, other_feature is not thermal, so it stays?
        # Re-check logic: exclude_collinear_thermal_features only drops thermal features.
        # 'other_feature' is not thermal, so it should remain.
        # Let's adjust the test expectation.
        assert 'other_feature' in result.columns