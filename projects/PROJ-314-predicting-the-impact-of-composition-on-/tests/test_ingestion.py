"""
Tests for ingestion module, specifically T018 clean_data functionality and T014 imputation logic.
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

def test_clean_data_imputation_group_vs_global():
    """
    Test T014: Imputation logic specifically distinguishing between 
    group median (by primary_anion_cation_group) and global median.
    """
    data = {
        'composition': ['ZrO2', 'HfO2', 'Al2O3', 'MgO'],
        'weibull_modulus': [10.0, 12.0, 15.0, 18.0],
        'mean_atomic_radius': [1.5, np.nan, 1.4, np.nan], # Missing in Group 1 and Group 2
        'primary_anion_cation_group': ['Group1', 'Group1', 'Group2', 'Group2'],
        'N': [50, 50, 50, 50]
    }
    df = pd.DataFrame(data)
    
    # Group1 values: 1.5 (ZrO2), NaN (HfO2). Median of Group1 is 1.5.
    # Group2 values: 1.4 (Al2O3), NaN (MgO). Median of Group2 is 1.4.
    # If group logic works, HfO2 should get 1.5, MgO should get 1.4.
    
    result = clean_data(df)
    
    # Verify no NaNs remain in the target column
    assert not result['mean_atomic_radius'].isna().any()
    assert 'is_imputed' in result.columns
    
    # Find the rows for HfO2 and MgO
    hf_row = result[result['composition'] == 'HfO2'].iloc[0]
    mg_row = result[result['composition'] == 'MgO'].iloc[0]
    
    # HfO2 is in Group1. Group1 median (non-missing) is 1.5.
    assert abs(hf_row['mean_atomic_radius'] - 1.5) < 1e-6, \
        f"Expected HfO2 (Group1) to be imputed with group median 1.5, got {hf_row['mean_atomic_radius']}"
    
    # MgO is in Group2. Group2 median (non-missing) is 1.4.
    assert abs(mg_row['mean_atomic_radius'] - 1.4) < 1e-6, \
        f"Expected MgO (Group2) to be imputed with group median 1.4, got {mg_row['mean_atomic_radius']}"
    
    # Verify the is_imputed flag is set correctly
    assert hf_row['is_imputed'] == True
    assert mg_row['is_imputed'] == True

def test_clean_data_imputation_fallback_global():
    """
    Test T014: When a group has ALL values missing, fallback to global median.
    """
    data = {
        'composition': ['ZrO2', 'HfO2', 'Al2O3', 'MgO'],
        'weibull_modulus': [10.0, 12.0, 15.0, 18.0],
        # All Group1 values are missing
        'mean_atomic_radius': [np.nan, np.nan, 1.4, 1.6], 
        'primary_anion_cation_group': ['Group1', 'Group1', 'Group2', 'Group2'],
        'N': [50, 50, 50, 50]
    }
    df = pd.DataFrame(data)
    
    # Group1: NaN, NaN -> Median is NaN -> Fallback to Global Median.
    # Global non-missing values: 1.4, 1.6. Median = 1.5.
    # So both HfO2 and ZrO2 should get 1.5.
    
    result = clean_data(df)
    
    assert not result['mean_atomic_radius'].isna().any()
    
    zr_row = result[result['composition'] == 'ZrO2'].iloc[0]
    hf_row = result[result['composition'] == 'HfO2'].iloc[0]
    
    assert abs(zr_row['mean_atomic_radius'] - 1.5) < 1e-6, \
        f"Expected ZrO2 to fallback to global median 1.5, got {zr_row['mean_atomic_radius']}"
    assert abs(hf_row['mean_atomic_radius'] - 1.5) < 1e-6, \
        f"Expected HfO2 to fallback to global median 1.5, got {hf_row['mean_atomic_radius']}"

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