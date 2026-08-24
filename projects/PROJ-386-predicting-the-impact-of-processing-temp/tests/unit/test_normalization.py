import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data.preprocessing import normalize_features

def test_normalize_features_basic():
    """Test that normalize_features correctly scales numeric columns."""
    # Create a simple dataframe
    data = {
        'temp': [100.0, 200.0, 300.0, 400.0],
        'Mg': [1.0, 2.0, 3.0, 4.0],
        'Si': [0.5, 1.0, 1.5, 2.0],
        'grain_size': [50.0, 60.0, 70.0, 80.0],  # Target, should not be scaled
        'alloy_series': ['A', 'B', 'A', 'B']  # Categorical, not scaled
    }
    df = pd.DataFrame(data)
    
    # Run normalization
    df_scaled, stats = normalize_features(df)
    
    # Verify scaling stats
    assert 'temp' in stats
    assert 'Mg' in stats
    assert 'Si' in stats
    
    # Check means are ~0
    assert abs(df_scaled['temp'].mean()) < 1e-6
    assert abs(df_scaled['Mg'].mean()) < 1e-6
    assert abs(df_scaled['Si'].mean()) < 1e-6
    
    # Check stds are ~1
    assert abs(df_scaled['temp'].std() - 1.0) < 1e-6
    assert abs(df_scaled['Mg'].std() - 1.0) < 1e-6
    assert abs(df_scaled['Si'].std() - 1.0) < 1e-6
    
    # Verify target and categorical were NOT scaled
    # (They should retain original values)
    assert df_scaled['grain_size'].equals(df['grain_size'])
    assert df_scaled['alloy_series'].equals(df['alloy_series'])

def test_normalize_features_empty():
    """Test behavior with no numeric columns to scale."""
    data = {
        'grain_size': [10.0, 20.0],
        'alloy_series': ['A', 'B']
    }
    df = pd.DataFrame(data)
    
    df_scaled, stats = normalize_features(df)
    
    # Should return same dataframe and empty stats
    assert df_scaled.equals(df)
    assert stats == {}

def test_normalize_features_verification_assert():
    """Test that the function asserts if scaling fails."""
    # This is a sanity check; the function should assert internally.
    # We just ensure it doesn't crash on valid data.
    data = {
        'temp': [100.0, 200.0],
        'Mg': [1.0, 2.0],
        'grain_size': [50.0, 60.0]
    }
    df = pd.DataFrame(data)
    
    # Should not raise
    df_scaled, stats = normalize_features(df)
    assert len(df_scaled) == 2
    assert 'temp' in df_scaled.columns
    assert 'Mg' in df_scaled.columns