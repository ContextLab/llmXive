"""
Tests for code/download.py

These tests verify that the download logic is present and correctly
structured to fail on missing data (no synthetic fallback).
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path if not already
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from download import main, OUTPUT_FILE, OUTPUT_DIR, DATASET_ID, FILENAME

def test_download_module_imports():
    """Verify that the download module can be imported."""
    # If we are here, the import succeeded in the test setup
    assert DATASET_ID == "osf/reproducibility_project"
    assert FILENAME == "data.csv"

@patch('download.hf_hub_download')
@patch('download.shutil.copy2')
@patch('download.OUTPUT_FILE')
def test_download_success_flow(mock_output_file, mock_copy, mock_download):
    """Test the successful path of the download function."""
    # Setup mocks
    mock_download.return_value = "/tmp/fake/downloaded_data.csv"
    mock_output_file.exists.return_value = True
    mock_output_file.stat.return_value.st_size = 1024
    
    # Mock hashlib to avoid actual file reading in test
    with patch('download.hashlib.sha256') as mock_hashlib:
        mock_hash = MagicMock()
        mock_hash.hexdigest.return_value = "abc123"
        mock_hashlib.return_value = mock_hash
        
        # Mock the open context manager for hash calculation
        mock_file = MagicMock()
        mock_file.read.return_value = b""
        mock_file.__enter__ = lambda s: mock_file
        mock_file.__exit__ = lambda s, *args: None
        
        with patch('builtins.open', return_value=mock_file):
            result = main()
            
    assert result == 0
    mock_download.assert_called_once()
    mock_copy.assert_called_once()

@patch('download.hf_hub_download')
def test_download_failure_no_fallback(mock_download, capsys):
    """
    Test that the download fails loudly when the real source is unavailable.
    It must NOT generate synthetic data or return success.
    """
    # Simulate a failure in the real fetch
    mock_download.side_effect = Exception("Connection timeout or file not found")
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    # Verify exit code is 1 (failure)
    assert exc_info.value.code == 1
    
    # Verify error message indicates real data requirement
    captured = capsys.readouterr()
    assert "ERROR" in captured.err
    assert "real data" in captured.err.lower()
    assert "synthetic" in captured.err.lower()