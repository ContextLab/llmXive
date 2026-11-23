"""
Unit tests for code/ingestion/validate_fingerprints.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from ingestion.validate_fingerprints import (
    validate_no_nulls,
    validate_fingerprint_dimension,
    validate_dataset
)

@pytest.fixture
def sample_dataframe():
    """Create a mock dataframe with valid data."""
    dim = 2048
    data = {
        "smiles": ["CCO", "CC(=O)O", "c1ccccc1"],
        "space_group": ["P212121", "P212121", "Fm-3m"],
        "a": [10.0, 10.0, 10.0],
        "b": [10.0, 10.0, 10.0],
        "c": [10.0, 10.0, 10.0],
        "alpha": [90.0, 90.0, 90.0],
        "beta": [90.0, 90.0, 90.0],
        "gamma": [90.0, 90.0, 90.0],
        "fingerprint": [
            [1] * dim,
            [0] * dim,
            [1 if i % 2 == 0 else 0 for i in range(dim)]
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_dataframe_nulls():
    """Create a mock dataframe with nulls."""
    dim = 2048
    data = {
        "smiles": ["CCO", None, "c1ccccc1"],
        "space_group": ["P212121", "P212121", None],
        "fingerprint": [
            [1] * dim,
            [0] * dim,
            [1] * dim
        ]
    }
    return pd.DataFrame(data)

@pytest.fixture
def sample_dataframe_wrong_dim():
    """Create a mock dataframe with wrong fingerprint dimension."""
    dim = 100 # Wrong dimension
    data = {
        "smiles": ["CCO"],
        "space_group": ["P212121"],
        "fingerprint": [[1] * dim]
    }
    return pd.DataFrame(data)

def test_validate_no_nulls_pass(sample_dataframe):
    """Test that valid data passes null check."""
    key_cols = ["smiles", "space_group", "a"]
    result = validate_no_nulls(sample_dataframe, key_cols)
    assert result["passed"] is True
    assert len(result["issues"]) == 0

def test_validate_no_nulls_fail(sample_dataframe_nulls):
    """Test that data with nulls fails."""
    key_cols = ["smiles", "space_group"]
    result = validate_no_nulls(sample_dataframe_nulls, key_cols)
    assert result["passed"] is False
    assert len(result["issues"]) > 0
    assert "smiles" in result["details"] or "space_group" in result["details"]

def test_validate_fingerprint_dimension_pass(sample_dataframe):
    """Test that correct dimension passes."""
    result = validate_fingerprint_dimension(sample_dataframe, "fingerprint", 2048)
    assert result["passed"] is True
    assert result["details"]["expected_dimension"] == 2048

def test_validate_fingerprint_dimension_fail_wrong_dim(sample_dataframe_wrong_dim):
    """Test that wrong dimension fails."""
    result = validate_fingerprint_dimension(sample_dataframe_wrong_dim, "fingerprint", 2048)
    assert result["passed"] is False
    assert "Expected dim 2048, got 100" in result["issues"][0]

def test_validate_fingerprint_dimension_fail_low_dim(sample_dataframe_wrong_dim):
    """Test that low dimension (even if consistent) fails magnitude check."""
    # Create a dataframe with dim=50
    dim = 50
    df = pd.DataFrame({
        "fingerprint": [[1]*dim]
    })
    result = validate_fingerprint_dimension(df, "fingerprint", 2048)
    assert result["passed"] is False
    assert "Average fingerprint dimension is 50.0" in result["issues"][0]

def test_validate_dataset_integration(sample_dataframe, tmp_path):
    """Integration test for the full validation pipeline."""
    # Save temp CSV
    csv_path = tmp_path / "test_dataset.csv"
    sample_dataframe.to_csv(csv_path, index=False)
    
    output_path = tmp_path / "check.json"
    
    # Mock get_path functions locally for this test
    import ingestion.validate_fingerprints as vf_module
    original_get_path_processed = vf_module.get_path_processed_data
    original_get_path_validation = vf_module.get_path_validation
    
    def mock_get_processed(name):
        return csv_path
    def mock_get_validation(name):
        return output_path
    
    vf_module.get_path_processed_data = mock_get_processed
    vf_module.get_path_validation = mock_get_validation
    
    try:
        result = validate_dataset(csv_path, output_path)
        
        assert result["status"] == "passed"
        assert output_path.exists()
        
        with open(output_path) as f:
            saved_result = json.load(f)
            assert saved_result["status"] == "passed"
    finally:
        # Restore
        vf_module.get_path_processed_data = original_get_path_processed
        vf_module.get_path_validation = original_get_path_validation
