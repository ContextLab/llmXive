"""Tests for standardization module."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

from standardize import (
    convert_k_to_half_life,
    standardize_dataset,
    generate_data_characteristics_table,
    check_data_coverage
)
from error_handlers import StatisticalInsufficiencyError

def test_k_to_half_life_conversion():
    """Test conversion from rate constant to half-life."""
    # t1/2 = ln(2) / k
    k = 0.01
    expected_t12 = np.log(2) / k
    actual_t12 = convert_k_to_half_life(k)
    assert abs(actual_t12 - expected_t12) < 0.01

def test_k_to_half_life_invalid():
    """Test that invalid k values raise an error."""
    with pytest.raises(ValueError):
        convert_k_to_half_life(0)
    
    with pytest.raises(ValueError):
        convert_k_to_half_life(-0.01)

def test_standardize_dataset_valid():
    """Test standardization with valid data."""
    # Create a mock dataset
    data = {
        'smiles': ['CCO', 'CCCO', 'CCCCO'],
        'half_life': [10.0, 20.0, 30.0],
        'temperature': [25.0, 25.0, 25.0],
        'ph': [7.4, 7.4, 7.4]
    }
    df = pd.DataFrame(data)
    
    # This should work if we have enough data
    # For this test, we'll mock the insufficiency check
    standard_subset, excluded = standardize_dataset(df)
    
    assert 'is_included' in standard_subset.columns
    assert 'derivation_source' in standard_subset.columns
    assert all(standard_subset['is_included'] == True)

def test_standardize_dataset_insufficient():
    """Test that insufficient data raises an error."""
    # Create a dataset with fewer than 30 records
    data = {
        'smiles': [f'CCO{i}' for i in range(10)],
        'half_life': [float(i) for i in range(10, 20)],
    }
    df = pd.DataFrame(data)
    
    with pytest.raises(StatisticalInsufficiencyError):
        standardize_dataset(df)

def test_generate_data_characteristics_table():
    """Test generation of data characteristics table."""
    # Create mock excluded records
    excluded = pd.DataFrame({
        'smiles': ['CCO', 'CCCO'],
        'temperature': [30.0, 35.0],
        'ph': [7.0, 6.5]
    })
    
    char_table = generate_data_characteristics_table(excluded)
    
    assert len(char_table) > 0
    assert 'reason' in char_table.columns or 'exclusion_reason' in char_table.columns

def test_check_data_coverage():
    """Test data coverage checking."""
    data = {
        'smiles': ['CCO', 'CCCO', 'CCCCO'],
        'half_life': [10.0, 20.0, None],
        'temperature': [25.0, 30.0, 25.0],
        'ph': [7.4, 7.4, 6.0]
    }
    df = pd.DataFrame(data)
    
    coverage = check_data_coverage(df)
    
    assert coverage['total_records'] == 3
    assert coverage['missing_half_life'] == 1
    assert coverage['missing_temperature'] == 0
    assert coverage['missing_ph'] == 0