import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from features import calculate_vif, filter_high_vif

def test_calculate_vif():
    """Test VIF calculation with known collinearity."""
    # Create a dataframe with perfect collinearity
    data = {
        'A': [1, 2, 3, 4, 5],
        'B': [2, 4, 6, 8, 10],  # Perfectly correlated with A
        'C': [1, 2, 3, 4, 5]   # Perfectly correlated with A
    }
    df = pd.DataFrame(data)
    
    vif_df = calculate_vif(df)
    
    assert 'feature' in vif_df.columns
    assert 'VIF' in vif_df.columns
    # With perfect collinearity, VIF should be very high or infinite (or raise error in some implementations)
    # statsmodels might return inf or a very large number
    assert len(vif_df) == 3
    # Check that at least one feature has high VIF
    assert any(vif_df['VIF'] > 10) or any(np.isinf(vif_df['VIF']))

def test_filter_high_vif():
    """Test filtering of high VIF features."""
    # Create a dataframe with one feature having high VIF
    data = {
        'X1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'X2': [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1], # Highly correlated
        'X3': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100], # Independent
        'target': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    }
    df = pd.DataFrame(data)
    
    filtered_df = filter_high_vif(df, threshold=5.0, exclude_cols=['target'])
    
    # X1 and X2 are highly correlated, one should be dropped
    assert len(filtered_df.columns) < len(df.columns)
    # Check that the filtered feature list file was created
    assert Path("data/processed/filtered_features.csv").exists()

def test_filter_high_vif_no_drop():
    """Test when no features exceed threshold."""
    data = {
        'X1': [1, 2, 3, 4, 5],
        'X2': [5, 4, 3, 2, 1], # Negatively correlated but not perfectly
        'X3': [1, 3, 5, 7, 9]
    }
    df = pd.DataFrame(data)
    
    # With random-ish data, VIF might be low
    filtered_df = filter_high_vif(df, threshold=50.0, exclude_cols=[])
    
    # All features should remain
    assert set(filtered_df.columns) == set(df.columns)
    assert Path("data/processed/filtered_features.csv").exists()
