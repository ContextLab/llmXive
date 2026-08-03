import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from data.derive_roles import (
    calculate_functional_role,
    verify_exclusion_of_co_occurrence,
    load_marginal_frequencies,
    load_positional_ranks
)

@pytest.fixture
def sample_marginal_freq():
    return pd.DataFrame({
        'ingredient_normalized': ['flour', 'sugar', 'salt', 'vanilla'],
        'marginal_frequency': [0.8, 0.6, 0.4, 0.2]
    })

@pytest.fixture
def sample_positional_ranks():
    return pd.DataFrame({
        'ingredient_normalized': ['flour', 'sugar', 'salt', 'vanilla'],
        'positional_rank': [1, 2, 3, 4]
    })

@pytest.fixture
def sample_co_occurrence():
    return pd.DataFrame({
        'ingredient_normalized': ['flour', 'sugar', 'salt', 'vanilla'],
        'log_co_occurrence': [2.5, 2.0, 1.5, 1.0]
    })

def test_calculate_functional_role_primary():
    """Test that high frequency and early rank result in primary role."""
    role = calculate_functional_role(
        marginal_freq=0.9,
        positional_rank=1,
        co_occurrence_count=0
    )
    assert role == 'primary'

def test_calculate_functional_role_secondary():
    """Test that medium frequency/rank result in secondary role."""
    role = calculate_functional_role(
        marginal_freq=0.5,
        positional_rank=3,
        co_occurrence_count=0
    )
    assert role == 'secondary'

def test_calculate_functional_role_garnish():
    """Test that low frequency and late rank result in garnish role."""
    role = calculate_functional_role(
        marginal_freq=0.1,
        positional_rank=10,
        co_occurrence_count=0
    )
    assert role == 'garnish'

def test_verify_exclusion_of_co_occurrence():
    """Test that verification function works correctly."""
    df_result = pd.DataFrame({
        'ingredient_normalized': ['a', 'b', 'c'],
        'functional_role': ['primary', 'secondary', 'garnish'],
        'log_co_occurrence': [2.5, 2.0, 1.5]
    })
    
    co_occurrence_matrix = pd.DataFrame({
        'ingredient_normalized': ['a', 'b', 'c'],
        'log_co_occurrence': [2.5, 2.0, 1.5]
    })
    
    result = verify_exclusion_of_co_occurrence(df_result, co_occurrence_matrix)
    
    assert 'correlation' in result
    assert 'passed' in result
    assert isinstance(result['correlation'], (float, type(None)))

def test_load_marginal_frequencies_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_marginal_frequencies('nonexistent_path.csv')

def test_load_positional_ranks_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_positional_ranks('nonexistent_path.csv')
