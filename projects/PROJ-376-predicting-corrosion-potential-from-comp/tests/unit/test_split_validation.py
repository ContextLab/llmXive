import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
import tempfile

# Mock the config to avoid file system dependencies during unit tests
@pytest.fixture
def mock_config():
    with patch('code.data.split.get_processed_data_path') as mock_get_path, \
         patch('code.data.split.get_log_path') as mock_get_log:
        mock_get_path.return_value = Path("/fake/path/corrosion_dataset.parquet")
        mock_get_log.return_value = Path("/fake/path/logs")
        yield

@pytest.fixture
def sample_df():
    """Create a sample DataFrame with distinct alloy groups."""
    # Create 15 unique alloys, 10 samples each
    alloys = [f"ALLOY_{i:03d}" for i in range(15)]
    data = []
    for alloy in alloys:
        for _ in range(10):
            data.append({
                "specific_alloy_designation_id": alloy,
                "pH": 7.0,
                "temp": 25.0,
                "corrosion_rate": 0.5,
                "Cr": 10.0,
                "Ni": 8.0
            })
    return pd.DataFrame(data)

@pytest.fixture
def mock_parquet_loader(sample_df):
    with patch('pandas.read_parquet', return_value=sample_df):
        yield

def test_validate_split_integrity_no_overlap(sample_df, mock_parquet_loader, mock_config):
    """Test that valid splits report zero overlap."""
    from code.data.split import perform_groupkfold_split, validate_split_integrity

    splits = perform_groupkfold_split(sample_df, n_splits=5, random_state=42)
    results = validate_split_integrity(splits, sample_df)

    assert results["global_overlap_check"] is True
    assert len(results["split_stats"]) == 5
    for stat in results["split_stats"]:
        assert stat["overlap_count"] == 0
        assert stat["is_valid"] is True

def test_validate_split_integrity_with_overlap():
    """
    Test detection of overlap when we manually craft a bad split.
    """
    from code.data.split import validate_split_integrity

    # Create a small DF with 3 alloys
    data = []
    for i in range(3):
        for _ in range(4):
            data.append({
                "specific_alloy_designation_id": f"ALG_{i}",
                "val": i
            })
    df = pd.DataFrame(data)

    # Craft a bad split: Fold 0 has ALG_0 in both train and test
    # Train indices: 0, 1 (ALG_0)
    # Test indices: 2, 3 (ALG_0)
    bad_splits = [
        ([0, 1], [2, 3]), 
        ([4, 5], [6, 7]),
        ([8, 9], [10, 11]),
        ([0, 4], [1, 5]), # Another overlap
        ([2, 6], [3, 7])
    ]

    results = validate_split_integrity(bad_splits, df)

    assert results["global_overlap_check"] is False
    assert results["details"]
    assert any("Fold 0" in d for d in results["details"])

def test_save_split_results(tmp_path, sample_df, mock_parquet_loader, mock_config):
    """Test that results are saved to JSON correctly."""
    from code.data.split import perform_groupkfold_split, validate_split_integrity, save_split_results

    splits = perform_groupkfold_split(sample_df, n_splits=5, random_state=42)
    results = validate_split_integrity(splits, sample_df)
    
    output_file = tmp_path / "test_split.json"
    save_split_results(results, output_file)

    assert output_file.exists()
    with open(output_file, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data["total_splits"] == 5
    assert "split_stats" in saved_data