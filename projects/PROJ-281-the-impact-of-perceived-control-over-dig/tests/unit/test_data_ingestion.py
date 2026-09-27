"""
Unit tests for data_ingestion module.
Note: This test mocks the HuggingFace download to avoid network dependency in unit tests.
It validates the logic of checksum computation, file validation, and data structure checks
without requiring network access or real data files.
"""
import hashlib
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

import pandas as pd

# Ensure the code directory is in the path for imports during testing
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.services.data_ingestion import (
    compute_sha256,
    validate_checksum,
    DataFetchError,
    # We will mock the actual download logic, so we don't import the full pipeline here
)

@patch("code.services.data_ingestion.load_dataset")
@patch("code.services.data_ingestion.RAW_DATA_DIR")
@patch("code.services.data_ingestion.BASE_DIR")
def test_download_dataset_success(mock_base_dir, mock_raw_dir, mock_load_dataset, tmp_path):
    """Test successful download and save of dataset structure."""
    # Setup mocks
    mock_raw_dir.__truediv__ = lambda self, other: tmp_path / other
    mock_raw_dir.exists = lambda: True
    mock_raw_dir.mkdir = lambda *args, **kwargs: None
    mock_base_dir.__truediv__ = lambda self, other: tmp_path.parent / other
    mock_base_dir.exists = lambda: True

    # Mock dataset object
    mock_dataset = MagicMock()
    # Use a smaller subset for the mock to simulate the sampling logic if needed,
    # but here we just test the structure validation
    mock_dataset.to_pandas.return_value = pd.DataFrame({
        "id": [1, 2, 3],
        "text": ["test text 1", "test text 2", "test text 3"],
        "label": [0, 1, 0],
        "timestamp": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "user_id": ["u1", "u2", "u3"]
    })
    mock_load_dataset.return_value = mock_dataset

    # Import after patching to ensure mocks are active
    from code.services.data_ingestion import download_and_validate_dataset

    # Execute
    # Note: We pass a mock path for output to ensure it writes to tmp_path
    output_path, checksum = download_and_validate_dataset(output_dir=tmp_path)

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
    mock_base_dir.__truediv__ = lambda self, other: tmp_path.parent / other

    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = pd.DataFrame({
        "content": ["no id here"],
        "timestamp": ["2023-01-01"]
    })
    mock_load_dataset.return_value = mock_dataset

    from code.services.data_ingestion import download_and_validate_dataset

    with pytest.raises(ValueError, match="missing required 'text' column"):
        download_and_validate_dataset(output_dir=tmp_path)

def test_compute_sha256(tmp_path):
    """Test SHA256 checksum computation."""
    test_file = tmp_path / "test.txt"
    test_content = b"hello world"
    test_file.write_bytes(test_content)

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

    assert validate_checksum(test_file, checksum_file) is True

@patch("code.services.data_ingestion.RAW_DATA_DIR")
def test_validate_checksum_mismatch(mock_raw_dir, tmp_path):
    """Test checksum validation failure on mismatch."""
    mock_raw_dir.__truediv__ = lambda self, other: tmp_path / other

    test_file = tmp_path / "social_media.csv"
    test_file.write_bytes(b"test data")

    checksum_file = tmp_path / "social_media.sha256"
    checksum_file.write_text("wrong_checksum")

    assert validate_checksum(test_file, checksum_file) is False

@patch("code.services.data_ingestion.load_dataset")
@patch("code.services.data_ingestion.RAW_DATA_DIR")
@patch("code.services.data_ingestion.BASE_DIR")
def test_download_dataset_empty(mock_base_dir, mock_raw_dir, mock_load_dataset, tmp_path):
    """Test handling of empty dataset."""
    mock_raw_dir.__truediv__ = lambda self, other: tmp_path / other
    mock_raw_dir.exists = lambda: True
    mock_raw_dir.mkdir = lambda *args, **kwargs: None
    mock_base_dir.__truediv__ = lambda self, other: tmp_path.parent / other

    mock_dataset = MagicMock()
    mock_dataset.to_pandas.return_value = pd.DataFrame(columns=["id", "text", "label"])
    mock_load_dataset.return_value = mock_dataset

    from code.services.data_ingestion import download_and_validate_dataset

    with pytest.raises(ValueError, match="Dataset is empty"):
        download_and_validate_dataset(output_dir=tmp_path)

@patch("code.services.data_ingestion.load_dataset")
@patch("code.services.data_ingestion.RAW_DATA_DIR")
@patch("code.services.data_ingestion.BASE_DIR")
def test_download_dataset_network_error(mock_base_dir, mock_raw_dir, mock_load_dataset, tmp_path):
    """Test handling of network error during download."""
    mock_raw_dir.__truediv__ = lambda self, other: tmp_path / other
    mock_raw_dir.exists = lambda: True
    mock_raw_dir.mkdir = lambda *args, **kwargs: None
    mock_base_dir.__truediv__ = lambda self, other: tmp_path.parent / other

    mock_load_dataset.side_effect = Exception("Network error")

    from code.services.data_ingestion import download_and_validate_dataset, DataFetchError

    with pytest.raises(DataFetchError):
        download_and_validate_dataset(output_dir=tmp_path)