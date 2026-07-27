"""
Unit tests for save_model_results.py (T033).
Tests verify the structure of the output and the integration of sensitivity data.
"""
import os
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# We need to import the main logic functions
# Since save_model_results.py has a main() that runs the whole pipeline,
# we will test the helper functions or mock the heavy parts.
from code.save_model_results import (
    load_sensitivity_analysis,
    train_models_and_get_r2,
    prepare_data_and_split
)

@pytest.fixture
def temp_sensitivity_file(tmp_path):
    file_path = tmp_path / "sensitivity.json"
    data = [
        {"threshold": 3.0, "r2": 0.85, "kruskal_stat": 1.2, "kruskal_pval": 0.5},
        {"threshold": 3.5, "r2": 0.82, "kruskal_stat": 2.1, "kruskal_pval": 0.3}
    ]
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return str(file_path)

def test_load_sensitivity_analysis(temp_sensitivity_file):
    """Test loading sensitivity analysis JSON."""
    data = load_sensitivity_analysis(temp_sensitivity_file)
    assert isinstance(data, list)
    assert len(data) == 2
    assert "threshold" in data[0]
    assert "r2" in data[0]
    assert "kruskal_stat" in data[0]
    assert "kruskal_pval" in data[0]

def test_load_sensitivity_analysis_file_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_sensitivity_analysis("non_existent_path.json")

def test_train_models_and_get_r2():
    """Test that training functions return correct R2 scores."""
    # Create dummy data
    X_train = np.random.rand(100, 5)
    y_train = np.random.rand(100)
    X_test = np.random.rand(20, 5)
    y_test = np.random.rand(20)
    
    metrics = train_models_and_get_r2(X_train, y_train, X_test, y_test, seed=42)
    
    assert "rf_r2" in metrics
    assert "gb_r2" in metrics
    assert isinstance(metrics["rf_r2"], float)
    assert isinstance(metrics["gb_r2"], float)
    # R2 can be negative, but for random data it's usually around 0 or negative.
    # We just check it's a number.
    assert np.isfinite(metrics["rf_r2"])
    assert np.isfinite(metrics["gb_r2"])

@patch('code.save_model_results.load_and_validate_target')
@patch('code.save_model_results.scaffold_split')
@patch('code.save_model_results.pd.read_csv')
def test_prepare_data_and_split(mock_read_csv, mock_scaffold_split, mock_validate_target, tmp_path):
    """Test data preparation and splitting logic."""
    # Setup mocks
    mock_df = pd.DataFrame({
        'smiles': ['C1', 'C2', 'C3', 'C4'],
        'status': ['valid', 'valid', 'valid', 'valid'],
        'feature1': [1.0, 2.0, 3.0, 4.0],
        'feature2': [5.0, 6.0, 7.0, 8.0],
        'conductivity': [1.0, 2.0, 3.0, 4.0]
    })
    mock_read_csv.return_value = mock_df
    mock_validate_target.return_value = (mock_df, 'conductivity')
    mock_scaffold_split.return_value = ([0, 1], [2, 3])

    # Call function
    # We need to mock the file existence check or create a dummy file
    descriptors_path = os.path.join("data", "processed", "descriptors.csv")
    # Create a dummy file if it doesn't exist in the test env
    os.makedirs("data/processed", exist_ok=True)
    with open(descriptors_path, 'w') as f:
        mock_df.to_csv(f, index=False)

    try:
        X_train, X_test, y_train, y_test, df = prepare_data_and_split()
        
        assert len(X_train) == 2
        assert len(X_test) == 2
        assert len(y_train) == 2
        assert len(y_test) == 2
        assert df is not None
    finally:
        # Cleanup
        if os.path.exists(descriptors_path):
            os.remove(descriptors_path)
        # Remove the directory if empty (optional)
        # os.rmdir("data/processed") # Might fail if not empty
        # os.rmdir("data") # Might fail if not empty