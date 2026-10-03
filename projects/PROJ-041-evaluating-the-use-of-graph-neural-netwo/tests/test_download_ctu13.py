"""
Tests for the CTU-13 download script.

These tests verify the logic of the download script without actually downloading
the full dataset in the test environment (mocking network calls).
"""
import os
import sys
import pytest
import hashlib
from unittest.mock import patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from data.download_ctu13 import (
    calculate_sha256, 
    download_file, 
    validate_file, 
    trigger_fallback, 
    main,
    OUTPUT_DIR,
    MIN_FILE_SIZE_BYTES
)

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_file.csv"
    file_path.write_text("Flow Id,duration,label\n1,10,1\n2,20,0\n")
    return str(file_path)

def test_calculate_sha256(temp_file):
    """Test SHA256 calculation."""
    hash_val = calculate_sha256(temp_file)
    assert len(hash_val) == 64  # SHA256 hex length
    assert isinstance(hash_val, str)

def test_download_file_success(tmp_path):
    """Test successful download mocking."""
    dest = str(tmp_path / "downloaded.csv")
    with patch('urllib.request.urlretrieve') as mock_url:
        mock_url.return_value = (dest, None)
        result = download_file("http://example.com/file.csv", dest)
        assert result is True
        mock_url.assert_called_once()

def test_download_file_failure(tmp_path):
    """Test failed download mocking."""
    dest = str(tmp_path / "downloaded.csv")
    with patch('urllib.request.urlretrieve') as mock_url:
        mock_url.side_effect = Exception("Network Error")
        result = download_file("http://example.com/file.csv", dest)
        assert result is False

def test_validate_file_valid(temp_file):
    """Test validation of a valid file."""
    # Ensure file is large enough for the mock (override min size for test)
    with patch('data.download_ctu13.MIN_FILE_SIZE_BYTES', 10):
        assert validate_file(temp_file) is True

def test_validate_file_too_small(tmp_path):
    """Test validation of a file that is too small."""
    small_file = tmp_path / "small.csv"
    small_file.write_text("a")
    with patch('data.download_ctu13.MIN_FILE_SIZE_BYTES', 100):
        assert validate_file(str(small_file)) is False

def test_validate_file_missing():
    """Test validation of a missing file."""
    assert validate_file("nonexistent_file.csv") is False

def test_main_success(monkeypatch, tmp_path):
    """Test main function success path with mocked download."""
    # Setup paths
    os.makedirs(tmp_path, exist_ok=True)
    monkeypatch.setattr('data.download_ctu13.OUTPUT_DIR', str(tmp_path))
    monkeypatch.setattr('data.download_ctu13.MIN_FILE_SIZE_BYTES', 10)
    
    # Mock the download to create a dummy file
    dummy_content = "Flow Id,duration,label\n1,10,1\n" * 1000
    with patch('data.download_ctu13.download_file') as mock_dl:
        def create_dummy(url, dest):
            Path(dest).write_text(dummy_content)
            return True
        mock_dl.side_effect = create_dummy
        
        # Mock state update to avoid file system errors
        with patch('data.download_ctu13.load_state', return_value={}):
            with patch('data.download_ctu13.update_state'):
                main()
        
        # Check if file was created
        expected_file = os.path.join(str(tmp_path), "ctu13_scenario_1.csv")
        assert os.path.exists(expected_file)

def test_main_failure_triggers_fallback(monkeypatch, tmp_path):
    """Test main function failure path triggers fallback."""
    os.makedirs(tmp_path, exist_ok=True)
    monkeypatch.setattr('data.download_ctu13.OUTPUT_DIR', str(tmp_path))
    
    # Mock download to fail
    with patch('data.download_ctu13.download_file', return_value=False):
        with patch('data.download_ctu13.trigger_fallback') as mock_fallback:
            with pytest.raises(RuntimeError, match="CTU-13 dataset fetch failed"):
                main()
            mock_fallback.assert_called_once()