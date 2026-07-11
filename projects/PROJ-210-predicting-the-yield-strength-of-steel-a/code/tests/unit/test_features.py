import pytest
import pandas as pd
import numpy as np
from src.data.features import calculate_elemental_ratios, calculate_pairwise_interactions, orthogonalize_spline, engineer_features

def test_calculate_elemental_ratios():
    df = pd.DataFrame({'C': [0.1, 0.2], 'Mn': [1.0, 2.0], 'Cr': [10.0, 20.0], 'Ni': [5.0, 10.0]})
    result = calculate_elemental_ratios(df)
    assert 'C_Mn_ratio' in result.columns
    assert 'Cr_Ni_ratio' in result.columns
    assert np.isclose(result['C_Mn_ratio'].iloc[0], 0.1)

def test_calculate_pairwise_interactions():
    df = pd.DataFrame({
        'cooling_rate': [10.0, 20.0],
        'holding_time': [5.0, 10.0],
        'C': [0.1, 0.2]
    })
    result = calculate_pairwise_interactions(df)
    # Check for generated interaction columns
    assert any('cooling_rate_x_holding_time' in c for c in result.columns)
    assert any('C_x_cooling_rate' in c for c in result.columns)

def test_orthogonalize_spline():
    x = np.linspace(0, 10, 100)
    y = x**2 + np.random.normal(0, 0.5, 100)
    residuals = orthogonalize_spline(x, y, degree=3, knots=5)
    assert len(residuals) == len(x)
    # Check if residuals are centered (roughly)
    assert np.abs(np.mean(residuals)) < 1.0

def test_engineer_features():
    df = pd.DataFrame({
        'C': [0.1, 0.2],
        'Mn': [1.0, 2.0],
        'cooling_rate': [10.0, 20.0],
        'holding_time': [5.0, 10.0],
        'yield_strength': [500.0, 600.0]
    })
    result = engineer_features(df)
    assert result.shape[1] > df.shape[1] # Should have added features