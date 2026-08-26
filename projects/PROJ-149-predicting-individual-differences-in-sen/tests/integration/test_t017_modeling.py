"""
Integration test for T017: Modeling Pipeline.
Verifies that the script runs, produces outputs, and validates schema.
"""
import os
import sys
import json
import pytest
import pandas as pd
from pathlib import Path

# Add code directory to path if needed
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from config import get_path

@pytest.mark.integration
def test_t017_script_execution():
    """
    Test that 05_modeling.py runs without error and produces expected files.
    This test assumes the pipeline up to T012c has been run successfully.
    """
    # Check prerequisites
    features_path = get_path("data/processed/features.csv")
    assert os.path.exists(features_path), "Prerequisite T012c (features.csv) not found."
    
    # Run the script
    import subprocess
    script_path = code_dir / "05_modeling.py"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Check outputs exist
    split_path = get_path("data/interim/split_indices.json")
    results_path = get_path("data/processed/model_results.json")
    
    assert os.path.exists(split_path), "Split indices file not created."
    assert os.path.exists(results_path), "Model results file not created."

@pytest.mark.integration
def test_model_results_schema():
    """
    Verify the schema of data/processed/model_results.json.
    """
    results_path = get_path("data/processed/model_results.json")
    if not os.path.exists(results_path):
        pytest.skip("Model results file not found (run T017 first).")
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    required_keys = [
        'adjusted_r2', 'optimal_lambda', 'rmse', 
        'test_r2', 'test_rmse'
    ]
    
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
        assert isinstance(data[key], (int, float)), f"Key {key} must be numeric."
    
    # Check for non-null optimal_lambda if it's a LASSO result
    # LASSO should always have a lambda value
    assert data['optimal_lambda'] is not None, "optimal_lambda cannot be None for LASSO."

@pytest.mark.integration
def test_split_indices_schema():
    """
    Verify the schema of data/interim/split_indices.json.
    """
    split_path = get_path("data/interim/split_indices.json")
    if not os.path.exists(split_path):
        pytest.skip("Split indices file not found (run T017 first).")
    
    with open(split_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ['train_indices', 'test_indices', 'train_size', 'test_size']
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    assert isinstance(data['train_indices'], list), "train_indices must be a list."
    assert isinstance(data['test_indices'], list), "test_indices must be a list."
    assert len(data['train_indices']) == data['train_size'], "train_size mismatch."
    assert len(data['test_indices']) == data['test_size'], "test_size mismatch."
    assert data['train_size'] + data['test_size'] > 0, "No data split."

@pytest.mark.integration
def test_data_integrity():
    """
    Ensure that the split indices correspond to valid participant IDs in the features file.
    """
    features_path = get_path("data/processed/features.csv")
    split_path = get_path("data/interim/split_indices.json")
    
    if not os.path.exists(features_path) or not os.path.exists(split_path):
        pytest.skip("Prerequisite files missing.")
    
    df = pd.read_csv(features_path)
    with open(split_path, 'r') as f:
        splits = json.load(f)
    
    train_ids = set(splits['train_indices'])
    test_ids = set(splits['test_indices'])
    all_ids = set(df['participant_id'].astype(str))
    
    # Check for overlap
    assert len(train_ids & test_ids) == 0, "Train and test sets overlap!"
    
    # Check that all split IDs are in the features file
    # Note: participant_id might be int in file and str in JSON, so we cast
    # The split indices are loaded as strings from JSON if they were ints, 
    # but the file might be int. Let's normalize.
    df_ids = set(df['participant_id'].astype(str))
    
    missing_in_train = train_ids - df_ids
    missing_in_test = test_ids - df_ids
    
    assert len(missing_in_train) == 0, f"Train IDs not in features: {missing_in_train}"
    assert len(missing_in_test) == 0, f"Test IDs not in features: {missing_in_test}"
