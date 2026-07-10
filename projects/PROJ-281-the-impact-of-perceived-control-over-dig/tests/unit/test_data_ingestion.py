"""
Unit tests for data_ingestion module.
Note: This test mocks the HuggingFace download to avoid network dependency in unit tests.
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

import pandas as pd
import pytest

# Import the module to test
# We need to handle the import of code.config if it's not fully set up in test env
# For unit tests, we often mock the config or set up a temporary one.
# Here we assume code.config exists as per T004.

# Patch the dataset loading to avoid network calls
@patch("code.services.data_ingestion.load_dataset")
@patch("code.services.data_ingestion.RAW_DATA_DIR")
@patch("code.services.data_ingestion.BASE_DIR")
def test_download_dataset_success(mock_base_dir, mock_raw_dir, mock_load_dataset, tmp_path):
    """Test successful download and save of dataset."""
    # Setup mocks
    mock_raw_dir.__truediv__ = lambda self, other: tmp_path / other
    mock_raw_dir.exists = lambda: True
    mock_raw_dir.mkdir = lambda *args, **kwargs: None
    
    # Mock dataset object
    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = pd.DataFrame({
        "id": [1, 2, 3],
        "text": ["test text 1", "test text 2", "test text 3"],
        "label": [0, 1, 0]
    })
    mock_load_dataset.return_value = mock_dataset
    
    # Import after patching
    from code.services.data_ingestion import download_dataset
    
    # Execute
    output_path, checksum = download_dataset()
    
    # Assertions
    assert output_path.exists()
    assert output_path.name == "social_media.csv"
    assert checksum is not None
    assert len(checksum) == 64  # SHA256 hex length
    
    # Verify content
    df = pd.read_csv(output_path)
    assert len(df) == 3
    assert "text" in df.columns
    assert "id" in df.columns

@patch("code.services.data_ingestion.load_dataset")
@patch("code.services.data_ingestion.RAW_DATA_DIR")
@patch("code.services.data_ingestion.BASE_DIR")
def test_download_dataset_missing_columns(mock_base_dir, mock_raw_dir, mock_load_dataset, tmp_path):
    """Test handling of dataset missing required columns."""
    mock_raw_dir.__truediv__ = lambda self, other: tmp_path / other
    mock_raw_dir.exists = lambda: True
    mock_raw_dir.mkdir = lambda *args, **kwargs: None
    
    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = pd.DataFrame({
        "content": ["no id here"]
    })
    mock_load_dataset.return_value = mock_dataset
    
    from code.services.data_ingestion import download_dataset
    
    with pytest.raises(ValueError, match="missing required 'text' column"):
        download_dataset()

def test_compute_sha256(tmp_path):
    """Test SHA256 checksum computation."""
    test_file = tmp_path / "test.txt"
    test_content = b"hello world"
    test_file.write_bytes(test_content)
    
    from code.services.data_ingestion import compute_sha256
    
    checksum = compute_sha256(test_file)
    expected = hashlib.sha256(test_content).hexdigest()
    
    assert checksum == expected

@patch("code.services.data_ingestion.RAW_DATA_DIR")
def test_validate_checksum_success(mock_raw_dir, tmp_path):
    """Test successful checksum validation."""
    mock_raw_dir.__truediv__ = lambda self, other: tmp_path / other
    
    # Create a file
    test_file = tmp_path / "social_media.csv"
    content = b"test data"
    test_file.write_bytes(content)
    
    # Create checksum file
    checksum = hashlib.sha256(content).hexdigest()
    checksum_file = tmp_path / "social_media.sha256"
    checksum_file.write_text(checksum)
    
    from code.services.data_ingestion import validate_checksum
    
    assert validate_checksum(test_file, checksum_file) is True

@patch("code.services.data_ingestion.RAW_DATA_DIR")
def test_validate_checksum_mismatch(mock_raw_dir, tmp_path):
    """Test checksum validation failure on mismatch."""
    mock_raw_dir.__truediv__ = lambda self, other: tmp_path / other
    
    test_file = tmp_path / "social_media.csv"
    test_file.write_bytes(b"test data")
    
    checksum_file = tmp_path / "social_media.sha256"
    checksum_file.write_text("wrong_checksum")
    
    from code.services.data_ingestion import validate_checksum
    
    assert validate_checksum(test_file, checksum_file) is False
