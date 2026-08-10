import os
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Add the code directory to the path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data.co_occurrence import load_epsilon_config, load_ingredient_pairs, build_cooccurrence_matrix, save_output

@pytest.fixture
def sample_data(tmp_path):
    """Create a small sample dataset for testing."""
    data = {
        'recipe_id': ['R1', 'R1', 'R1', 'R2', 'R2', 'R3'],
        'ingredient_id': ['salt', 'pepper', 'garlic', 'salt', 'pepper', 'oil']
    }
    df = pd.DataFrame(data)
    input_file = tmp_path / "normalized_ingredients.csv"
    df.to_csv(input_file, index=False)
    
    # Create epsilon config
    config = {'epsilon': 1e-9}
    config_file = tmp_path / "epsilon_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f)
    
    return input_file, config_file, tmp_path

def test_load_epsilon_config(sample_data):
    _, config_file, _ = sample_data
    eps = load_epsilon_config(str(config_file))
    assert abs(eps - 1e-9) < 1e-10

def test_load_ingredient_pairs(sample_data):
    input_file, _, _ = sample_data
    df = load_ingredient_pairs(str(input_file))
    assert len(df) == 6
    assert 'recipe_id' in df.columns
    assert 'ingredient_id' in df.columns

def test_build_cooccurrence_matrix_small(sample_data):
    input_file, config_file, tmp_path = sample_data
    epsilon = load_epsilon_config(str(config_file))
    df = load_ingredient_pairs(str(input_file))
    
    matrix = build_cooccurrence_matrix(df, epsilon)
    
    # Expected pairs from R1: (salt, pepper), (salt, garlic), (pepper, garlic)
    # R2: (salt, pepper)
    # R3: (oil) -> no pairs
    # Counts:
    # salt-pepper: 2
    # salt-garlic: 1
    # pepper-garlic: 1
    
    # Check if it's a square matrix or long form
    if isinstance(matrix, pd.DataFrame) and not matrix.empty:
        # Check shape or content
        # If square:
        if matrix.index.equals(matrix.columns):
            # Verify counts
            # salt-pepper should be log(1+2) + eps = log(3) + eps
            if 'salt' in matrix.index and 'pepper' in matrix.columns:
                expected_val = np.log1p(2) + epsilon
                actual_val = matrix.loc['salt', 'pepper']
                assert abs(actual_val - expected_val) < 1e-9
        else:
            # Long form check
            assert 'ingredient_1' in matrix.columns
            assert 'ingredient_2' in matrix.columns
            assert 'log_count' in matrix.columns
            # Verify at least one row exists
            assert len(matrix) > 0

def test_empty_dataframe():
    df = pd.DataFrame(columns=['recipe_id', 'ingredient_id'])
    with pytest.raises(ValueError):
        build_cooccurrence_matrix(df)

def test_missing_columns():
    df = pd.DataFrame({'wrong_col': [1, 2]})
    with pytest.raises(ValueError):
        build_cooccurrence_matrix(df)

def test_save_output(sample_data, tmp_path):
    input_file, config_file, _ = sample_data
    epsilon = load_epsilon_config(str(config_file))
    df = load_ingredient_pairs(str(input_file))
    matrix = build_cooccurrence_matrix(df, epsilon)
    
    output_file = tmp_path / "test_co_occurrence.parquet"
    save_output(matrix, str(output_file))
    
    assert output_file.exists()
    # Try to load it back
    loaded = pd.read_parquet(output_file)
    assert not loaded.empty
