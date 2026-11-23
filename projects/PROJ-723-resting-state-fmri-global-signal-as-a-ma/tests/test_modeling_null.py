import pytest
import numpy as np
import pandas as pd
import json
import os
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score

# Import functions to test
# Assuming the functions are in code/modeling.py
# We need to add code/ to sys.path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from modeling import run_null_distribution_analysis, load_cleaned_data, prepare_model_data

@pytest.fixture
def sample_data(tmp_path):
    """Create a small sample dataset for testing."""
    data = {
        'Subject_ID': range(1, 21),
        'Global_Signal_SD': np.random.rand(20) * 10,
        'MWQ_Score': np.random.rand(20) * 100,
        'Age': np.random.randint(18, 65, 20),
        'Sex': np.random.choice([0, 1], 20),
        'Mean_FD': np.random.rand(20) * 0.5,
        'Mean_DVARS': np.random.rand(20) * 10
    }
    df = pd.DataFrame(data)
    file_path = tmp_path / "cleaned_data.csv"
    df.to_csv(file_path, index=False)
    return str(file_path), df

def test_null_distribution_generation(sample_data):
    """Test that null distribution is generated correctly."""
    file_path, df = sample_data
    X, y, _ = prepare_model_data(df)
    observed_mae = 10.0 # Fake observed for test
    
    # Run with small N for speed
    results = run_null_distribution_analysis(
        X, y, observed_mae, 
        min_permutations=5, max_permutations=10, target_std=100.0 # High target to stop early
    )
    
    assert 'null_maes' in results
    assert 'n_permutations' in results
    assert results['n_permutations'] >= 5
    assert len(results['null_maes']) == results['n_permutations']
    
    # Check p-value calculation
    assert 'p_value_mae' in results
    assert 0 <= results['p_value_mae'] <= 1

def test_permutation_logic(sample_data):
    """Test that permutation actually changes the data."""
    file_path, df = sample_data
    X, y, _ = prepare_model_data(df)
    
    # Run a single permutation manually to verify
    rng = np.random.RandomState(42)
    y_permuted = rng.permutation(y)
    
    assert not np.array_equal(y, y_permuted)
    assert np.array_equal(np.sort(y), np.sort(y_permuted))
    
    # Run the analysis and ensure it doesn't crash
    results = run_null_distribution_analysis(
        X, y, 10.0, 
        min_permutations=2, max_permutations=2, target_std=100.0
    )
    assert results['n_permutations'] == 2

def test_null_distribution_file_creation(tmp_path, sample_data):
    """Test that the null distribution file is created with correct structure."""
    # This test is more of an integration test for the file writing
    # We simulate the main logic here
    file_path, df = sample_data
    X, y, _ = prepare_model_data(df)
    
    results = run_null_distribution_analysis(
        X, y, 10.0, 
        min_permutations=2, max_permutations=2, target_std=100.0
    )
    
    # Verify structure
    assert 'null_maes' in results
    assert isinstance(results['null_maes'], list)
    assert all(isinstance(x, float) for x in results['null_maes'])
    assert 'p_value_mae' in results
    assert isinstance(results['p_value_mae'], float)