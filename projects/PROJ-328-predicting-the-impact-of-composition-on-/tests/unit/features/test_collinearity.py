"""
Unit tests for collinearity diagnostics.
"""
import numpy as np
import pandas as pd
import pytest
from code.features.collinearity import calculate_vif

def test_vif_calculation():
    """Test VIF calculation on a dataset with no collinearity."""
    # Create a dataset with low collinearity
    data = {
        'A': np.random.rand(100),
        'B': np.random.rand(100),
        'C': np.random.rand(100)
    }
    df = pd.DataFrame(data)
    
    vif_scores, high_vif = calculate_vif(df)
    
    assert len(vif_scores) == 3
    assert len(high_vif) == 0  # Should be no high VIF

def test_vif_high_collinearity():
    """Test VIF calculation on a dataset with high collinearity."""
    # Create a dataset with high collinearity (B is a multiple of A)
    A = np.random.rand(100)
    data = {
        'A': A,
        'B': A * 2,  # Perfect collinearity
        'C': np.random.rand(100)
    }
    df = pd.DataFrame(data)
    
    vif_scores, high_vif = calculate_vif(df)
    
    # B should have infinite or very high VIF
    # Note: statsmodels might return NaN or inf for perfect collinearity
    assert 'B' in vif_scores
    assert vif_scores['B'] >= 5.0 or np.isinf(vif_scores['B']) or np.isnan(vif_scores['B'])

def test_vif_empty_dataframe():
    """Test VIF calculation on an empty dataframe."""
    df = pd.DataFrame()
    vif_scores, high_vif = calculate_vif(df)
    
    assert vif_scores == {}
    assert high_vif == []