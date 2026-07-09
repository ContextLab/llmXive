"""
Unit tests for preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
from code.preprocessing import map_elemental_composition_to_features, handle_missing_values

def test_map_elemental_composition_to_features_basic():
    """Test basic mapping with known elements."""
    data = {
        'Fe': [70.0, 60.0],
        'Cr': [20.0, 25.0],
        'Ni': [10.0, 15.0],
        'id': [1, 2]  # Non-elemental column
    }
    df = pd.DataFrame(data)
    
    result = map_elemental_composition_to_features(df)
    
    # Should only contain elemental columns
    expected_cols = {'Cr', 'Fe', 'Ni'}
    assert set(result.columns) == expected_cols
    
    # Should be normalized to sum to 1.0
    assert np.isclose(result.sum(axis=1).iloc[0], 1.0, atol=1e-6)
    assert np.isclose(result.sum(axis=1).iloc[1], 1.0, atol=1e-6)
    
    # Columns should be sorted
    assert list(result.columns) == sorted(result.columns)

def test_map_elemental_composition_to_features_missing_elements():
    """Test mapping when some standard elements are missing from input."""
    data = {
        'Fe': [100.0],
        'Ni': [0.0]
    }
    df = pd.DataFrame(data)
    
    # Should not raise an error, just use available elements
    result = map_elemental_composition_to_features(df)
    
    assert 'Fe' in result.columns
    assert 'Ni' in result.columns
    assert np.isclose(result['Fe'].iloc[0], 1.0)
    assert np.isclose(result['Ni'].iloc[0], 0.0)

def test_map_elemental_composition_to_features_missing_values():
    """Test mapping with missing values (NaN) in elemental columns."""
    data = {
        'Fe': [70.0, np.nan],
        'Cr': [20.0, 20.0],
        'Ni': [10.0, 80.0]
    }
    df = pd.DataFrame(data)
    
    result = map_elemental_composition_to_features(df)
    
    # Missing values should be treated as 0.0
    # Row 1: 0 + 20 + 80 = 100 -> Fe=0, Cr=0.2, Ni=0.8
    assert np.isclose(result['Fe'].iloc[1], 0.0)
    assert np.isclose(result['Cr'].iloc[1], 0.2, atol=1e-6)
    assert np.isclose(result['Ni'].iloc[1], 0.8, atol=1e-6)

def test_handle_missing_values_imputation():
    """Test that missing values < 5% are imputed with median."""
    data = {
        'A': [1.0, 2.0, np.nan, 4.0, 5.0],  # 1/5 = 20% missing -> drop
        'B': [1.0, 2.0, 3.0, 4.0, np.nan],  # 1/5 = 20% missing -> drop
        'C': [1.0, 2.0, 3.0, 4.0, 5.0]      # 0% missing -> keep
    }
    # Actually, let's use a threshold of 0.3 (30%) to test imputation
    df = pd.DataFrame(data)
    cleaned, stats = handle_missing_values(df, threshold=0.3)
    
    assert 'C' in cleaned.columns
    assert stats['C']['action'] == 'kept'
    
    # A and B have 20% missing, which is < 30%, so they should be imputed
    assert 'A' in cleaned.columns
    assert stats['A']['action'] == 'imputed_median'
    assert 'B' in cleaned.columns
    assert stats['B']['action'] == 'imputed_median'

def test_handle_missing_values_dropping():
    """Test that missing values >= 5% cause column drop."""
    data = {
        'A': [1.0, np.nan, np.nan, np.nan, 5.0],  # 3/5 = 60% missing -> drop
        'B': [1.0, 2.0, 3.0, 4.0, 5.0]            # 0% missing -> keep
    }
    df = pd.DataFrame(data)
    cleaned, stats = handle_missing_values(df, threshold=0.05)
    
    assert 'B' in cleaned.columns
    assert stats['B']['action'] == 'kept'
    
    assert 'A' not in cleaned.columns
    assert stats['A']['action'] == 'dropped'

def test_no_standard_elements_found():
    """Test error when no standard elements are found."""
    data = {
        'id': [1, 2],
        'label': ['pitting', 'scc']
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(ValueError) as excinfo:
        map_elemental_composition_to_features(df)
    
    assert "No standard elemental columns found" in str(excinfo.value)
