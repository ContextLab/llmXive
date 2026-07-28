import os
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the module functions
from code.data.co_occurrence import load_epsilon_config, load_ingredient_pairs, build_cooccurrence_matrix, save_output, main

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

def test_load_epsilon_config_missing(temp_dir):
    """Test default epsilon when config is missing."""
    # Should return default 1e-10
    result = load_epsilon_config(os.path.join(temp_dir, "missing.json"))
    assert result == 1e-10

def test_load_epsilon_config_valid(temp_dir):
    """Test loading valid epsilon config."""
    config_path = os.path.join(temp_dir, "config.json")
    with open(config_path, 'w') as f:
        json.dump({"epsilon": 0.001}, f)
    
    result = load_epsilon_config(config_path)
    assert result == 0.001

def test_build_cooccurrence_matrix_basic(temp_dir):
    """Test basic matrix construction and log transform."""
    # Create dummy input data
    data = {
        'ingredient_id_1': ['A', 'A', 'B', 'B', 'C'],
        'ingredient_id_2': ['B', 'C', 'A', 'C', 'A'],
        'count': [10, 5, 10, 2, 2]
    }
    df = pd.DataFrame(data)
    
    epsilon = 1e-10
    matrix_df, stats = build_cooccurrence_matrix(df, epsilon)
    
    # Check stats
    assert stats['dimensions'][0] == 3 # 3 unique ingredients (A, B, C)
    assert stats['dimensions'][1] == 3
    assert 'sparsity' in stats
    assert 'mean_log_count' in stats
    
    # Check matrix values (log transform)
    # A-B: log(10 + eps) ~ 2.3
    # A-C: log(5 + eps) ~ 1.6
    # B-A: log(10 + eps) ~ 2.3
    # B-C: log(2 + eps) ~ 0.69
    # C-A: log(2 + eps) ~ 0.69
    
    # Verify the matrix is symmetric in terms of content if we consider the pairs
    # Note: The pivot creates a specific orientation.
    # We just verify that the values are positive and log-transformed.
    assert (matrix_df.iloc[:, 1:] > 0).all().all() # All log counts should be > 0 for count > 0

def test_save_output(temp_dir):
    """Test saving matrix and stats."""
    data = {
        'ingredient_id_1': ['A', 'B'],
        'A': [1.0, 0.0],
        'B': [0.0, 2.0]
    }
    # Create a dummy matrix DF
    matrix_df = pd.DataFrame(data)
    stats = {"test": 123}
    
    matrix_path = os.path.join(temp_dir, "matrix.parquet")
    stats_path = os.path.join(temp_dir, "stats.json")
    
    save_output(matrix_df, stats, matrix_path, stats_path)
    
    assert os.path.exists(matrix_path)
    assert os.path.exists(stats_path)
    
    loaded_df = pd.read_parquet(matrix_path)
    assert loaded_df.shape == matrix_df.shape
    
    with open(stats_path, 'r') as f:
        loaded_stats = json.load(f)
    assert loaded_stats == stats

def test_load_ingredient_pairs_missing_columns(temp_dir):
    """Test error handling for missing columns."""
    data = {
        'wrong_col_1': ['A'],
        'wrong_col_2': ['B'],
        'wrong_count': [10]
    }
    df = pd.DataFrame(data)
    input_path = os.path.join(temp_dir, "input.parquet")
    df.to_parquet(input_path)
    
    with pytest.raises(ValueError, match="Expected columns"):
        load_ingredient_pairs(input_path)
