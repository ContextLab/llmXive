import pytest
import pandas as pd
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.data.split_validation import validate_split_integrity, load_split_indices, load_processed_data
from utils.exceptions import DataInsufficientError

def test_validate_split_integrity_no_overlap():
    """Test that a clean split with no overlap returns PASS status."""
    # Create mock DataFrame with unique alloy IDs
    df = pd.DataFrame({
        "specific_alloy_designation_id": ["A1", "A1", "A2", "A2", "A3", "A3"]
    })
    
    # Mock split data: Fold 0 has A1 in train, A2 in test (no overlap)
    split_data = [
        {
            "fold_id": 0,
            "train_indices": [0, 1],
            "test_indices": [2, 3]
        }
    ]
    
    # Mock the return format expected by the function
    mock_split_result = {
        "folds": [
            {"train_indices": [0, 1], "test_indices": [2, 3]}
        ]
    }
    
    # Run validation
    results = validate_split_integrity(mock_split_result, df)
    
    assert results["global_status"] == "PASS"
    assert results["folds"][0]["overlap_count"] == 0
    assert results["folds"][0]["status"] == "PASS"

def test_validate_split_integrity_with_overlap():
    """Test that a split with alloy leakage returns FAIL status."""
    df = pd.DataFrame({
        "specific_alloy_designation_id": ["A1", "A1", "A1", "A2"]
    })
    
    # Mock split data: A1 appears in both train and test
    mock_split_result = {
        "folds": [
            {"train_indices": [0, 1], "test_indices": [2, 3]}
        ]
    }
    
    results = validate_split_integrity(mock_split_result, df)
    
    assert results["global_status"] == "FAIL"
    assert results["folds"][0]["overlap_count"] == 1
    assert results["folds"][0]["status"] == "FAIL"

def test_validate_split_integrity_missing_column():
    """Test that missing alloy column raises ValueError."""
    df = pd.DataFrame({
        "other_column": [1, 2, 3]
    })
    
    mock_split_result = {
        "folds": [
            {"train_indices": [0], "test_indices": [1]}
        ]
    }
    
    with pytest.raises(ValueError, match="Alloy column"):
        validate_split_integrity(mock_split_result, df, alloy_column="specific_alloy_designation_id")

@patch('code.data.split_validation.get_split_indices_path')
@patch('code.data.split_validation.get_processed_dataset_path')
def test_load_split_indices_success(mock_data_path, mock_indices_path, tmp_path):
    """Test successful loading of split indices."""
    # Create a temporary JSON file
    test_file = tmp_path / "splits.json"
    test_data = [{"fold_id": 0, "train": [1, 2], "test": [3, 4]}]
    test_file.write_text(json.dumps(test_data))
    
    mock_indices_path.return_value = test_file
    
    result = load_split_indices()
    assert isinstance(result, list)
    assert len(result) == 1
    
@patch('code.data.split_validation.get_processed_dataset_path')
def test_load_processed_data_success(mock_data_path, tmp_path):
    """Test successful loading of processed parquet data."""
    # Create a temporary parquet file
    test_file = tmp_path / "data.parquet"
    df = pd.DataFrame({"specific_alloy_designation_id": ["A1", "A2"]})
    df.to_parquet(test_file)
    
    mock_data_path.return_value = test_file
    
    result = load_processed_data()
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert "specific_alloy_designation_id" in result.columns
