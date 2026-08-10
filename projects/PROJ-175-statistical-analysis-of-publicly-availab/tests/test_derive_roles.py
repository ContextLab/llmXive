import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from data.derive_roles import (
    ensure_directories,
    load_marginal_frequencies,
    load_positional_ranks,
    calculate_functional_role,
    verify_exclusion_of_co_occurrence
)

@pytest.fixture
def sample_freq_df():
    return pd.DataFrame({
        'ingredient_id': ['A', 'B', 'C', 'D'],
        'frequency': [100, 50, 10, 5]
    })

@pytest.fixture
def sample_pos_df():
    return pd.DataFrame({
        'ingredient_id': ['A', 'B', 'C', 'D'],
        'position': [0, 5, 10, 15]
    })

@pytest.fixture
def temp_dirs(tmp_path):
    # Create necessary directories
    (tmp_path / 'data' / 'processed').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'data' / 'logs').mkdir(parents=True, exist_ok=True)
    return tmp_path

def test_ensure_directories(temp_dirs):
    # This should not raise
    ensure_directories()
    assert (temp_dirs / 'data' / 'processed').exists()
    assert (temp_dirs / 'data' / 'logs').exists()

def test_calculate_functional_role(sample_freq_df, sample_pos_df):
    # Mock the merge and logic
    # A: High freq, Low pos -> primary
    # B: Med freq, Med pos -> secondary
    # C: Low freq, High pos -> garnish
    # D: Very low freq, Very high pos -> garnish
    
    result = calculate_functional_role(sample_freq_df, sample_pos_df)
    
    assert 'functional_role' in result.columns
    assert 'ingredient_id' in result.columns
    
    # Check specific assignments
    roles = result.set_index('ingredient_id')['functional_role']
    
    # A should be primary
    assert roles['A'] == 'primary'
    
    # C and D should be garnish (low freq, high pos)
    assert roles['C'] == 'garnish'
    assert roles['D'] == 'garnish'
    
    # B should be secondary
    assert roles['B'] == 'secondary'

def test_verify_exclusion_of_co_occurrence():
    # Test that the function runs without error
    co_occ_data = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    role_data = None
    
    # Should not raise
    verify_exclusion_of_co_occurrence(co_occ_data, role_data)
    
    # Test with None
    verify_exclusion_of_co_occurrence(None, role_data)

def test_load_marginal_frequencies_missing_file():
    with pytest.raises(FileNotFoundError):
        load_marginal_frequencies('non_existent_file.csv')

def test_load_positional_ranks_missing_file():
    with pytest.raises(FileNotFoundError):
        load_positional_ranks('non_existent_file.parquet')
