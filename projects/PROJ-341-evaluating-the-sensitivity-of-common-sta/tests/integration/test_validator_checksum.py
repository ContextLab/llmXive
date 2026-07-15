import os
import json
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

# Import the functions to test
from code.analysis.validator import (
    compute_file_checksum,
    verify_dataset_checksum,
    save_simulation_metadata,
    load_simulation_metadata,
    METADATA_PATH
)

@pytest.fixture
def temp_csv_file(tmp_path):
    """Create a temporary CSV file for testing checksums."""
    file_path = tmp_path / "test_data.csv"
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    df.to_csv(file_path, index=False)
    return str(file_path)

@pytest.fixture
def temp_metadata_file(tmp_path):
    """Create a temporary metadata file."""
    file_path = tmp_path / "test_metadata.json"
    data = {"checksums": {}}
    with open(file_path, 'w') as f:
        json.dump(data, f)
    return str(file_path)

def test_compute_file_checksum(temp_csv_file):
    """Test that compute_file_checksum returns a valid SHA-256 hash."""
    checksum = compute_file_checksum(temp_csv_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_verify_dataset_checksum_updates_metadata(tmp_path, temp_csv_file):
    """Test that verify_dataset_checksum updates the metadata file."""
    # Setup: Create a fake metadata file
    metadata_path = tmp_path / "metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump({"checksums": {}}, f)
    
    # Patch the global METADATA_PATH
    with patch('code.analysis.validator.METADATA_PATH', str(metadata_path)):
        # Create a fake dataset file
        dataset_path = tmp_path / "fake_dataset.csv"
        pd.DataFrame({"x": [1]}).to_csv(dataset_path, index=False)
        
        # Mock os.path.exists to return True for our fake file
        original_exists = os.path.exists
        def mock_exists(path):
            if path == str(dataset_path):
                return True
            return original_exists(path)
        
        with patch('os.path.exists', mock_exists):
            result = verify_dataset_checksum("fake_dataset", filepath_override=str(dataset_path))
            
            # Load the updated metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            assert "fake_dataset" in metadata["checksums"]
            assert "checksum" in metadata["checksums"]["fake_dataset"]

def test_verify_dataset_checksum_fails_if_file_missing():
    """Test that verify_dataset_checksum raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        verify_dataset_checksum("non_existent_dataset")

def test_save_and_load_simulation_metadata(tmp_path):
    """Test saving and loading simulation metadata."""
    metadata_path = tmp_path / "test_meta.json"
    
    test_data = {
        "seeds": [123, 456],
        "config": {"n": 100},
        "checksums": {"ds": {"checksum": "abc"}}
    }
    
    # Save
    with patch('code.analysis.validator.METADATA_PATH', str(metadata_path)):
        save_simulation_metadata(test_data)
        
        # Load
        loaded_data = load_simulation_metadata()
        
        assert loaded_data == test_data
