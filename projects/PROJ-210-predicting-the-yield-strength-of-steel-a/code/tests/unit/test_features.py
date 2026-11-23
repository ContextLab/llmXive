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
    def test_calculate_c_mn_ratio(self):
        df = pd.DataFrame({'C': [0.1, 0.2], 'Mn': [1.0, 2.0]})
        result = calculate_elemental_ratios(df)
        assert 'C_Mn_ratio' in result.columns
        assert np.isclose(result['C_Mn_ratio'].iloc[0], 0.1)
        assert np.isclose(result['C_Mn_ratio'].iloc[1], 0.1)

    def test_division_by_zero_handling(self):
        df = pd.DataFrame({'C': [0.1], 'Mn': [0.0]})
        result = calculate_elemental_ratios(df)
        assert 'C_Mn_ratio' in result.columns
        assert result['C_Mn_ratio'].iloc[0] == 0.0

class TestPairwiseInteractions:
    def test_cooling_rate_holding_time(self):
        df = pd.DataFrame({'cooling_rate': [2.0, 4.0], 'holding_time': [10.0, 20.0]})
        result = calculate_pairwise_interactions(df)
        assert 'cooling_rate_x_holding_time' in result.columns
        assert result['cooling_rate_x_holding_time'].iloc[0] == 20.0

    def test_c_cooling_rate_interaction(self):
        df = pd.DataFrame({'C': [0.2], 'cooling_rate': [5.0]})
        result = calculate_pairwise_interactions(df)
        assert any('C' in c and 'cooling_rate' in c for c in result.columns)

class TestOrthogonalizeSpline:
    def test_orthogonalize_spline_residuals(self):
        x = np.array([1, 2, 3, 4, 5], dtype=float)
        y = np.array([2, 4, 6, 8, 10], dtype=float) # Perfect linear
        residuals = orthogonalize_spline(x, y)
        # Residuals should be close to zero for perfect fit
        assert np.allclose(residuals, 0.0, atol=1e-5)

class TestZeroVariance:
    def test_detect_zero_variance(self):
        df = pd.DataFrame({
            'a': [1, 1, 1],
            'b': [1, 2, 3],
            'c': ['x', 'x', 'x']
        })
        cols = detect_zero_variance_columns(df)
        assert 'a' in cols
        assert 'c' in cols
        assert 'b' not in cols

class TestEngineerFeatures:
    def test_full_pipeline(self):
        df = pd.DataFrame({
            'C': [0.1, 0.2],
            'Mn': [1.0, 2.0],
            'cooling_rate': [2.0, 4.0],
            'holding_time': [10.0, 20.0],
            'yield_strength': [100, 200]
        })
        result = engineer_features(df)
        assert 'C_Mn_ratio' in result.columns
        assert 'cooling_rate_x_holding_time' in result.columns
        # Check that zero variance columns are removed if any were added
        assert 'yield_strength' in result.columns # Should remain

class TestCollinearThermal:
    def test_exclude_collinear_thermal(self):
        # Create data with perfect correlation between two thermal columns
        df = pd.DataFrame({
            'temp_1': [100.0, 200.0, 300.0],
            'temp_2': [200.0, 400.0, 600.0], # Perfectly correlated (2x)
            'cooling_rate': [1.0, 2.0, 3.0],
            'yield_strength': [100, 200, 300]
        })
        result = exclude_collinear_thermal_features(df)
        # One of temp_1 or temp_2 should be dropped
        assert not ('temp_1' in result.columns and 'temp_2' in result.columns)
        assert 'cooling_rate' in result.columns