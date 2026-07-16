"""Unit tests for the loaders module, specifically checksumming functionality."""
import pytest
import pandas as pd
import numpy as np
import os
import json
import hashlib
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Import the module functions
from code.loaders import (
    _calculate_sha256,
    _load_checksums,
    _save_checksums,
    _verify_checksum,
    fetch_uci_dataset,
    load_dataset_from_path
)

class TestChecksumCalculation:
    """Tests for SHA256 hash calculation."""

    def test_calculate_sha256_known_value(self, tmp_path):
        """Test SHA256 calculation against a known value."""
        test_content = b"Hello, World!"
        expected_hash = hashlib.sha256(test_content).hexdigest()
        
        file_path = tmp_path / "test.txt"
        file_path.write_bytes(test_content)
        
        calculated_hash = _calculate_sha256(str(file_path))
        
        assert calculated_hash == expected_hash

    def test_calculate_sha256_empty_file(self, tmp_path):
        """Test SHA256 calculation on empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.touch()
        
        calculated_hash = _calculate_sha256(str(file_path))
        expected_hash = hashlib.sha256(b"").hexdigest()
        
        assert calculated_hash == expected_hash

class TestChecksumStorage:
    """Tests for checksum storage and retrieval."""

    def test_load_empty_checksums(self, tmp_path):
        """Test loading checksums when file doesn't exist."""
        with patch('code.loaders.CHECKSUM_FILE', str(tmp_path / "nonexistent.json")):
            checksums = _load_checksums()
            assert checksums == {}

    def test_load_valid_checksums(self, tmp_path):
        """Test loading valid checksums from file."""
        test_checksums = {"dataset1": "hash1", "dataset2": "hash2"}
        checksum_file = tmp_path / "checksums.json"
        checksum_file.write_text(json.dumps(test_checksums))
        
        with patch('code.loaders.CHECKSUM_FILE', str(checksum_file)):
            loaded = _load_checksums()
            assert loaded == test_checksums

    def test_save_checksums(self, tmp_path):
        """Test saving checksums to file."""
        test_checksums = {"dataset1": "hash1"}
        checksum_file = tmp_path / "checksums.json"
        
        with patch('code.loaders.CHECKSUM_FILE', str(checksum_file)):
            _save_checksums(test_checksums)
            
            assert checksum_file.exists()
            with open(checksum_file, 'r') as f:
                saved = json.load(f)
            assert saved == test_checksums

class TestChecksumVerification:
    """Tests for checksum verification logic."""

    def test_verify_new_dataset_stores_checksum(self, tmp_path):
        """Test that new datasets have their checksums stored."""
        test_content = b"Test data"
        file_path = tmp_path / "test.csv"
        file_path.write_bytes(test_content)
        
        checksum_file = tmp_path / "checksums.json"
        with patch('code.loaders.CHECKSUM_FILE', str(checksum_file)):
            result = _verify_checksum("new_dataset", str(file_path))
            
            assert result is True
            assert checksum_file.exists()
            with open(checksum_file, 'r') as f:
                stored = json.load(f)
            assert "new_dataset" in stored
            assert stored["new_dataset"] == hashlib.sha256(test_content).hexdigest()

    def test_verify_matching_checksum(self, tmp_path):
        """Test verification with matching checksum."""
        test_content = b"Test data"
        file_path = tmp_path / "test.csv"
        file_path.write_bytes(test_content)
        
        checksum_file = tmp_path / "checksums.json"
        stored_hash = hashlib.sha256(test_content).hexdigest()
        checksum_file.write_text(json.dumps({"existing_dataset": stored_hash}))
        
        with patch('code.loaders.CHECKSUM_FILE', str(checksum_file)):
            result = _verify_checksum("existing_dataset", str(file_path))
            assert result is True

    def test_verify_mismatched_checksum_raises_error(self, tmp_path):
        """Test that checksum mismatch raises ValueError."""
        test_content = b"Test data"
        file_path = tmp_path / "test.csv"
        file_path.write_bytes(test_content)
        
        checksum_file = tmp_path / "checksums.json"
        wrong_hash = hashlib.sha256(b"different data").hexdigest()
        checksum_file.write_text(json.dumps({"existing_dataset": wrong_hash}))
        
        with patch('code.loaders.CHECKSUM_FILE', str(checksum_file)):
            with pytest.raises(ValueError, match="Checksum mismatch"):
                _verify_checksum("existing_dataset", str(file_path))

class TestFetchWithChecksum:
    """Tests for fetch_uci_dataset with checksumming."""

    @patch('code.loaders.requests.get')
    @patch('code.loaders._verify_checksum')
    def test_fetch_stores_and_verifies(self, mock_verify, mock_get, tmp_path):
        """Test that fetch stores and verifies checksum."""
        mock_response = MagicMock()
        mock_response.text = "col1,col2\n1,2\n3,4"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        mock_verify.return_value = True

        # Create data/raw directory
        data_dir = tmp_path / "data" / "raw"
        data_dir.mkdir(parents=True)
        
        with patch('code.loaders.UCI_BASE_URL', 'http://test.com'):
            with patch('code.loaders.CHECKSUM_FILE', str(tmp_path / "checksums.json")):
                with patch('os.makedirs'):
                    df = fetch_uci_dataset("test_dataset", "test.csv")
                    
                    assert df is not None
                    assert len(df) == 2
                    mock_verify.assert_called_once()

    @patch('code.loaders.requests.get')
    def test_fetch_raises_on_404(self, mock_get, tmp_path):
        """Test that 404 errors are properly raised."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.side_effect = Exception("404 Client Error")
        
        with patch('code.loaders.requests.exceptions.HTTPError') as mock_http_error:
            mock_http_error.return_value.response.status_code = 404
            with pytest.raises(FileNotFoundError):
                fetch_uci_dataset("nonexistent", "file.csv")

class TestLoadFromPathWithChecksum:
    """Tests for load_dataset_from_path with checksumming."""

    def test_load_new_file_stores_checksum(self, tmp_path):
        """Test that loading a new file stores its checksum."""
        test_data = "col1,col2\n1,2\n3,4"
        file_path = tmp_path / "test.csv"
        file_path.write_text(test_data)
        
        checksum_file = tmp_path / "checksums.json"
        with patch('code.loaders.CHECKSUM_FILE', str(checksum_file)):
            df = load_dataset_from_path(str(file_path))
            
            assert df is not None
            assert len(df) == 2
            assert checksum_file.exists()
            with open(checksum_file, 'r') as f:
                stored = json.load(f)
            assert "test.csv" in stored

    def test_load_matching_checksum_succeeds(self, tmp_path):
        """Test loading file with matching stored checksum."""
        test_data = "col1,col2\n1,2\n3,4"
        file_path = tmp_path / "test.csv"
        file_path.write_text(test_data)
        
        checksum_file = tmp_path / "checksums.json"
        stored_hash = hashlib.sha256(test_data.encode()).hexdigest()
        checksum_file.write_text(json.dumps({"test.csv": stored_hash}))
        
        with patch('code.loaders.CHECKSUM_FILE', str(checksum_file)):
            df = load_dataset_from_path(str(file_path))
            assert df is not None

    def test_load_mismatched_checksum_raises_error(self, tmp_path):
        """Test that loading file with mismatched checksum raises error."""
        test_data = "col1,col2\n1,2\n3,4"
        file_path = tmp_path / "test.csv"
        file_path.write_text(test_data)
        
        checksum_file = tmp_path / "checksums.json"
        wrong_hash = hashlib.sha256(b"wrong data").hexdigest()
        checksum_file.write_text(json.dumps({"test.csv": wrong_hash}))
        
        with patch('code.loaders.CHECKSUM_FILE', str(checksum_file)):
            with pytest.raises(ValueError, match="Checksum mismatch"):
                load_dataset_from_path(str(file_path))