import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add code directory to path
sys.path.insert(0, 'code')

from data.download import calculate_sha256, download_oqmd_dataset

def test_calculate_sha256():
    """Test SHA-256 calculation on a known string."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test data")
        tmp_path = Path(tmp.name)
    
    try:
        expected_hash = hashlib.sha256(b"test data").hexdigest()
        actual_hash = calculate_sha256(tmp_path)
        assert actual_hash == expected_hash
    finally:
        os.unlink(tmp_path)

@patch('data.download.load_dataset')
def test_download_oqmd_dataset_success(mock_load_dataset):
    """Test successful download and materialization."""
    # Mock dataset
    mock_df = MagicMock()
    mock_df.shape = (100, 10)
    mock_load_dataset.return_value.to_pandas.return_value = mock_df
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = os.path.join(tmp_dir, "raw")
        checksum_dir = tmp_dir
        
        result_path = download_oqmd_dataset(output_dir, checksum_dir)
        
        # Verify file was created
        assert os.path.exists(result_path)
        assert result_path.name == "oqmd.parquet"
        
        # Verify checksum file
        checksum_file = os.path.join(checksum_dir, "checksums.json")
        assert os.path.exists(checksum_file)
        
        with open(checksum_file) as f:
            checksum_data = json.load(f)
        
        assert checksum_data["filename"] == "oqmd.parquet"
        assert "sha256" in checksum_data
        assert len(checksum_data["sha256"]) == 64  # SHA-256 hex length

@patch('data.download.load_dataset')
def test_download_oqmd_dataset_retry_logic(mock_load_dataset):
    """Test retry logic with exponential backoff."""
    # Fail first two attempts, succeed on third
    mock_df = MagicMock()
    mock_df.shape = (100, 10)
    
    side_effects = [
        ConnectionError("Network error"),
        ConnectionError("Network error"),
        mock_df
    ]
    mock_load_dataset.return_value.to_pandas.side_effect = side_effects
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = os.path.join(tmp_dir, "raw")
        checksum_dir = tmp_dir
        
        # Should succeed on 3rd attempt
        result_path = download_oqmd_dataset(output_dir, checksum_dir)
        
        # Verify load_dataset was called 3 times
        assert mock_load_dataset.call_count == 3
        assert os.path.exists(result_path)

@patch('data.download.load_dataset')
def test_download_oqmd_dataset_fails_loudly(mock_load_dataset):
    """Test that download fails loudly after max retries."""
    # Always fail
    mock_load_dataset.side_effect = ConnectionError("Persistent network error")
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = os.path.join(tmp_dir, "raw")
        checksum_dir = tmp_dir
        
        # Should raise exception after 3 attempts
        with pytest.raises(Exception):
            download_oqmd_dataset(output_dir, checksum_dir)
        
        # Verify load_dataset was called 3 times
        assert mock_load_dataset.call_count == 3