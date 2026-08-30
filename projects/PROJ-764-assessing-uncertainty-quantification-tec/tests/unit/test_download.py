import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add code to path if running as script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.download import download_oqmd_dataset

@patch('data.download.load_dataset')
@patch('data.download.Path')
def test_download_oqmd_dataset_success(mock_path, mock_load_dataset, tmp_path):
    """Test successful download and save."""
    # Setup mocks
    mock_dataset = MagicMock()
    mock_df = MagicMock()
    mock_dataset.to_pandas.return_value = mock_df
    mock_load_dataset.return_value = mock_dataset
    
    mock_output_path = MagicMock()
    mock_path.return_value = mock_output_path
    mock_output_path.exists.return_value = False
    mock_output_path.__truediv__.return_value = tmp_path / "oqmd.parquet"
    
    # Run
    result = download_oqmd_dataset(str(tmp_path))
    
    # Assertions
    mock_load_dataset.assert_called_once_with("oqmd/formation-energy", split="train", streaming=False)
    mock_dataset.to_pandas.assert_called_once()
    mock_df.to_parquet.assert_called_once()
    assert result.exists()

@patch('data.download.time.sleep')
@patch('data.download.load_dataset')
@patch('data.download.Path')
def test_download_oqmd_dataset_retry_logic(mock_path, mock_load_dataset, mock_sleep, tmp_path):
    """Test retry logic with exponential backoff."""
    # Setup mocks
    mock_output_path = MagicMock()
    mock_path.return_value = mock_output_path
    mock_output_path.exists.return_value = False
    
    # Make load_dataset fail twice then succeed
    mock_load_dataset.side_effect = [
        ConnectionError("Network error 1"),
        ConnectionError("Network error 2"),
        MagicMock(to_pandas=MagicMock(return_value=MagicMock()))
    ]
    
    # Run
    result = download_oqmd_dataset(str(tmp_path))
    
    # Assertions
    assert mock_load_dataset.call_count == 3
    assert mock_sleep.call_count == 2
    mock_sleep.assert_any_call(2)
    mock_sleep.assert_any_call(4)

@patch('data.download.time.sleep')
@patch('data.download.load_dataset')
@patch('data.download.Path')
def test_download_oqmd_dataset_fails_loudly(mock_path, mock_load_dataset, mock_sleep, tmp_path):
    """Test that the function raises after max retries."""
    # Setup mocks
    mock_output_path = MagicMock()
    mock_path.return_value = mock_output_path
    mock_output_path.exists.return_value = False
    
    # Make load_dataset fail every time
    mock_load_dataset.side_effect = ConnectionError("Persistent network error")
    
    # Run and assert exception
    with pytest.raises(Exception):
        download_oqmd_dataset(str(tmp_path))
    
    assert mock_load_dataset.call_count == 3
    assert mock_sleep.call_count == 2

@patch('data.download.Path')
def test_download_oqmd_dataset_skips_existing(mock_path, tmp_path):
    """Test that existing file is skipped."""
    mock_output_path = MagicMock()
    mock_path.return_value = mock_output_path
    existing_file = tmp_path / "oqmd.parquet"
    existing_file.touch()
    mock_output_path.exists.return_value = True
    
    result = download_oqmd_dataset(str(tmp_path))
    
    mock_output_path.exists.assert_called_once()
    assert result == existing_file
    # load_dataset should not be called
    from data.download import load_dataset
    # Note: load_dataset is imported at module level, so we check the mock
    # Since we patched the module's load_dataset, we can check it
    # However, in the function, it uses the imported name.
    # The patch on 'data.download.load_dataset' covers the usage inside the function.
    assert not mock_load_dataset.called