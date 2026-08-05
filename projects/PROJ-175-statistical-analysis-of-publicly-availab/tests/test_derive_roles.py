import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
import sys

# Add code to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.derive_roles import (
    ensure_directories,
    load_marginal_frequencies,
    load_positional_ranks,
    calculate_functional_role,
    verify_exclusion_of_co_occurrence,
    save_output
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    dirs = ['data/processed', 'data/logs']
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return tmp_path

@pytest.fixture
def mock_freq_data(temp_data_dir):
    """Create mock normalized_ingredients.csv."""
    data = {
        'ingredient_id': ['ing_1', 'ing_2', 'ing_3', 'ing_4', 'ing_5'],
        'canonical_name': ['salt', 'pepper', 'oil', 'garlic', 'basil'],
        'functional_role': ['primary', 'secondary', 'garnish', 'primary', 'garnish'],
        'frequency': [1000, 500, 200, 800, 100]
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / 'data' / 'processed' / 'normalized_ingredients.csv'
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def mock_rank_data(temp_data_dir):
    """Create mock positional_ranks.csv."""
    data = {
        'ingredient_id': ['ing_1', 'ing_2', 'ing_3', 'ing_4', 'ing_5'],
        'positional_rank': [1, 3, 5, 2, 4]
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / 'data' / 'processed' / 'positional_ranks.csv'
    df.to_csv(path, index=False)
    return path

@pytest.fixture
def mock_co_occ_data(temp_data_dir):
    """Create mock co_occurrence_matrix.parquet."""
    data = {
        'ingredient_a': ['ing_1', 'ing_1', 'ing_2', 'ing_3'],
        'ingredient_b': ['ing_2', 'ing_3', 'ing_3', 'ing_4'],
        'count': [500, 100, 200, 300]
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / 'data' / 'processed' / 'co_occurrence_matrix.parquet'
    df.to_parquet(path, index=False)
    return path

def test_ensure_directories(temp_data_dir):
    # Change to temp dir context
    old_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    try:
        ensure_directories()
        assert Path('data/processed').exists()
        assert Path('data/logs').exists()
    finally:
        os.chdir(old_cwd)

def test_load_marginal_frequencies(mock_freq_data, temp_data_dir):
    old_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    try:
        df = load_marginal_frequencies()
        assert 'ingredient_id' in df.columns
        assert 'frequency' in df.columns
        assert len(df) == 5
    finally:
        os.chdir(old_cwd)

def test_calculate_functional_role(mock_freq_data, mock_rank_data, temp_data_dir):
    old_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    try:
        df_freq = load_marginal_frequencies()
        df_ranks = load_positional_ranks()
        
        result = calculate_functional_role(df_freq, df_ranks)
        
        assert 'functional_role' in result.columns
        assert 'composite_score' in result.columns
        assert all(r in ['primary', 'secondary', 'garnish'] for r in result['functional_role'])
        
        # Check that high frequency/low rank gets 'primary'
        ing_1_role = result[result['ingredient_id'] == 'ing_1']['functional_role'].values[0]
        assert ing_1_role == 'primary', f"Expected 'primary' for ing_1, got {ing_1_role}"
    finally:
        os.chdir(old_cwd)

def test_verify_exclusion_of_co_occurrence(mock_freq_data, mock_rank_data, mock_co_occ_data, temp_data_dir):
    old_cwd = os.getcwd()
    os.chdir(temp_data_dir)
    try:
        df_freq = load_marginal_frequencies()
        df_ranks = load_positional_ranks()
        roles_df = calculate_functional_role(df_freq, df_ranks)
        co_occ_df = pd.read_parquet(mock_co_occ_data)
        
        # Should not raise
        result = verify_exclusion_of_co_occurrence(roles_df, co_occ_df)
        assert result is True
        
        # Check audit log exists
        assert Path('data/logs/role_independence_audit.json').exists()
    finally:
        os.chdir(old_cwd)
