"""
Tests for ingestion module, specifically T018 clean_data functionality.
"""
import pytest
import pandas as pd
import numpy as np
from code.ingestion import clean_data

def test_clean_data_filter_n():
    """Test that rows with N < 30 are filtered out."""
    data = {
        'composition': ['ZrO2', 'Al2O3', 'SiC'],
        'weibull_modulus': [10.0, 15.0, 20.0],
        'N': [20, 50, 10]
    }
    df = pd.DataFrame(data)
    result = clean_data(df)
    assert len(result) == 1
    assert result.iloc[0]['composition'] == 'Al2O3'
    assert 'sample_count' in result.columns

def test_clean_data_range_handling():
    """Test range value extraction and flagging."""
    data = {
        'composition': ['ZrO2'],
        'weibull_modulus': ['10-12'],
        'N': [50]
    }
    df = pd.DataFrame(data)
    result = clean_data(df)
    assert 'is_range_flag' in result.columns
    assert result['is_range_flag'].iloc[0] == True
    assert result['weibull_modulus'].iloc[0] == 11.0
    assert result['range_uncertainty'].iloc[0] == 1.0

def test_clean_data_imputation():
    """Test imputation of missing numeric values."""
    data = {
        'composition': ['ZrO2', 'Al2O3'],
        'weibull_modulus': [10.0, np.nan],
        'mean_atomic_radius': [1.5, np.nan],
        'N': [50, 60]
    }
    df = pd.DataFrame(data)
    result = clean_data(df)
    # Should not have NaN in numeric columns after imputation
    assert not result['mean_atomic_radius'].isna().any()
    assert not result['weibull_modulus'].isna().any()
    assert 'is_imputed' in result.columns

def test_clean_data_non_stoichiometric():
    """Test exclusion of non-stoichiometric compositions."""
    data = {
        'composition': ['ZrO2', 'ZrO2-x', 'Al2O3'],
        'weibull_modulus': [10.0, 15.0, 20.0],
        'N': [50, 50, 50]
    }
    df = pd.DataFrame(data)
    result = clean_data(df)
    assert len(result) == 2
    assert 'ZrO2-x' not in result['composition'].values

def test_clean_data_output_schema():
    """Test that all required output columns are present."""
    data = {
        'composition': ['ZrO2'],
        'weibull_modulus': [10.0],
        'N': [50],
        'sintering_temp': [1500.0],
        'primary_anion_cation_group': ['Group1'],
        'mean_atomic_radius': [1.5],
        'electronegativity_std': [0.5],
        'valence_electron_concentration': [4.0],
        'cation_size_variance': [0.1]
    }
    df = pd.DataFrame(data)
    result = clean_data(df)
    
    required_cols = [
        'composition', 'weibull_modulus', 'sample_count', 'is_range_flag', 
        'range_original', 'range_uncertainty', 'primary_anion_cation_group', 
        'mean_atomic_radius', 'electronegativity_std', 'valence_electron_concentration', 
        'cation_size_variance', 'sintering_temp', 'is_imputed'
    ]
    
    for col in required_cols:
        assert col in result.columns, f"Missing column: {col}"