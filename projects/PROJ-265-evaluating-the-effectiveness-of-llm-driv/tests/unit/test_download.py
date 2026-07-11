import os
import json
import hashlib
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.data.download import download_codesearchnet

# Import checksum utility from project root
from code.checksum import compute_sha256, should_exclude

# Define expected dataset metadata
DATASET_NAME = "codeparrot/codesearchnet-python"
EXPECTED_FILES = 1  # The dataset typically splits into train/validation/test, but download_codesearchnet usually saves one parquet per split or a combined one.
                    # Based on standard HuggingFace datasets usage in this project context, we expect at least the train split.
EXPECTED_MIN_FILES = 1
EXPECTED_CHECKSUM_KEY = "sha256"

@pytest.fixture
def mock_dataset():
    """Mock the datasets library to return a fake dataset object."""
    mock_dataset_obj = MagicMock()
    mock_dataset_obj["train"] = MagicMock()
    mock_dataset_obj["train"].to_parquet = MagicMock()
    return mock_dataset_obj

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure mimicking the project data folder."""
    data_dir = tmp_path / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def test_download_creates_directory_structure(temp_data_dir):
    """Test that download_codesearchnet creates the expected output directory."""
    with patch("code.data.download.load") as mock_load:
        # Mock the dataset loading
        mock_ds = MagicMock()
        mock_load.return_value = mock_ds
        
        # Mock the to_parquet method to actually create a file for the test
        def mock_to_parquet(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text("fake parquet content")
        
        mock_ds["train"].to_parquet = mock_to_parquet

        download_codesearchnet(str(temp_data_dir.parent))

        # Verify the directory exists
        assert temp_data_dir.exists()

def test_download_produces_parquet_file(temp_data_dir):
    """Test that the download process results in a parquet file."""
    with patch("code.data.download.load") as mock_load:
        mock_ds = MagicMock()
        mock_load.return_value = mock_ds
        
        def mock_to_parquet(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text("fake parquet content")
        
        mock_ds["train"].to_parquet = mock_to_parquet

        download_codesearchnet(str(temp_data_dir.parent))

        # Check for .parquet files
        parquet_files = list(temp_data_dir.glob("*.parquet"))
        assert len(parquet_files) >= EXPECTED_MIN_FILES, f"Expected at least {EXPECTED_MIN_FILES} parquet file, found {len(parquet_files)}"

def test_download_generates_checksum_file(temp_data_dir):
    """Test that a checksum file is generated alongside the data."""
    with patch("code.data.download.load") as mock_load:
        mock_ds = MagicMock()
        mock_load.return_value = mock_ds
        
        def mock_to_parquet(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text("fake parquet content")
        
        mock_ds["train"].to_parquet = mock_to_parquet

        download_codesearchnet(str(temp_data_dir.parent))

        # Check for .checksum.json file
        checksum_files = list(temp_data_dir.glob("*.checksum.json"))
        assert len(checksum_files) >= 1, "Expected a checksum file to be generated"

        # Verify content of checksum file
        checksum_file = checksum_files[0]
        with open(checksum_file, "r") as f:
            checksum_data = json.load(f)
        
        assert EXPECTED_CHECKSUM_KEY in checksum_data, "Checksum file missing 'sha256' key"
        assert isinstance(checksum_data[EXPECTED_CHECKSUM_KEY], str), "Checksum value should be a string"

def test_download_file_count_and_checksum_consistency(temp_data_dir):
    """Test that the checksum in the file matches the actual file content."""
    with patch("code.data.download.load") as mock_load:
        mock_ds = MagicMock()
        mock_load.return_value = mock_ds
        
        def mock_to_parquet(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            # Write deterministic content so checksum is predictable
            content = b"consistent_test_data_for_checksum_validation"
            Path(path).write_bytes(content)
        
        mock_ds["train"].to_parquet = mock_to_parquet

        download_codesearchnet(str(temp_data_dir.parent))

        # Locate the generated files
        parquet_files = list(temp_data_dir.glob("*.parquet"))
        checksum_files = list(temp_data_dir.glob("*.checksum.json"))

        assert len(parquet_files) == len(checksum_files), "Mismatch between parquet and checksum files"

        for pf, cf in zip(parquet_files, checksum_files):
            # Calculate actual checksum
            actual_hash = compute_sha256(pf)
            
            # Read recorded checksum
            with open(cf, "r") as f:
                recorded_data = json.load(f)
            
            recorded_hash = recorded_data.get("sha256")
            
            assert actual_hash == recorded_hash, f"Checksum mismatch for {pf.name}: expected {recorded_hash}, got {actual_hash}"

def test_download_uses_correct_dataset_name():
    """Test that the download function attempts to load the correct dataset."""
    with patch("code.data.download.load") as mock_load:
        mock_ds = MagicMock()
        mock_load.return_value = mock_ds
        
        def mock_to_parquet(path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text("content")
        
        mock_ds["train"].to_parquet = mock_to_parquet

        # Call the function
        download_codesearchnet("/tmp/fake_data")

        # Verify load was called with the correct dataset name
        mock_load.assert_called_once_with(DATASET_NAME)

def test_download_handles_missing_dataset_gracefully(temp_data_dir):
    """Test that the function handles dataset loading errors."""
    with patch("code.data.download.load") as mock_load:
        mock_load.side_effect = Exception("Dataset not found")
        
        # We expect the function to raise or log an error, but not crash silently
        # For this test, we verify it raises the exception as the logger might not be fully configured in test env
        with pytest.raises(Exception):
            download_codesearchnet(str(temp_data_dir.parent))